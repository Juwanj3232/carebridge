"""Run from the carebridge folder:  python3 -m unittest discover -s tests -v"""

import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

os.environ["CAREBRIDGE_DISABLE_AI"] = "1"          # tests never call the API
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import ai, auth, billing, fhir_export, followup, qa, safety, savings, store, summary   # noqa: E402
from backend.scenarios import SCENARIOS                                                   # noqa: E402


class SafetyScreen(unittest.TestCase):
    def test_red_flags_trigger_emergency_and_block_ai(self):
        for text in ["I have chest pain since this morning", "I can't breathe well", "I've been having suicidal thoughts",
                     "there is severe bleeding from the cut", "my face is drooping and I have slurred speech",
                     "Tengo dolor de pecho", "no puedo respirar"]:
            r = safety.screen(text)
            self.assertEqual(r.level, "emergency", text)
            self.assertFalse(r.ai_allowed)
            self.assertIn("911", r.patient_message["body"])

    def test_crisis_line_only_for_self_harm(self):
        self.assertIn("988", safety.screen("I want to kill myself").patient_message["crisis"])
        self.assertNotIn("crisis", safety.screen("chest pain").patient_message)

    def test_vague_wording_goes_to_nurse_review(self):
        r = safety.screen("my heart feels weird")
        self.assertEqual(r.level, "urgent_review")
        self.assertTrue(r.ai_allowed)
        self.assertIn("NURSE CHECK", r.staff_message)

    def test_negated_red_flag_is_reviewed_not_ignored(self):
        r = safety.screen("Ear hurts. No chest pain.")
        self.assertEqual(r.level, "urgent_review")
        self.assertEqual(safety.screen("no chest pain but I can't breathe").level, "emergency")

    def test_high_severity_alone_gets_review(self):
        self.assertEqual(safety.screen("my ankle hurts", severity=9).level, "urgent_review")

    def test_routine(self):
        for s in ("ear", "bp", "ankle"):
            self.assertEqual(safety.screen(SCENARIOS[s]["intake"]["symptoms"], SCENARIOS[s]["intake"]["severity"]).level, "routine", s)

    def test_spanish_message(self):
        self.assertIn("recepción", safety.screen("dolor de pecho", language="es").patient_message["title"])


class Billing(unittest.TestCase):
    def test_matches_prototype_ppo_generic(self):
        b = billing.breakdown("ppo", SCENARIOS["ear"]["outcome"], use_generic=True)
        self.assertEqual([i["patient"] for i in b["items"]], [30.0, 9.0, 2.8])
        self.assertEqual(b["total_patient"], 41.8)
        self.assertEqual(b["total_billed"], 204.0)
        self.assertEqual(b["generic_savings"], 12.8)

    def test_self_pay_discount_and_brand(self):
        b = billing.breakdown("self", SCENARIOS["ankle"]["outcome"], use_generic=False)
        self.assertEqual(b["items"][0]["patient"], 77.0)
        self.assertEqual(b["items"][2]["patient"], 64.0)

    def test_no_rx(self):
        b = billing.breakdown("ppo", SCENARIOS["heart"]["outcome"])
        self.assertEqual(len(b["items"]), 2)


class Summaries(unittest.TestCase):
    def test_rules_draft_has_footer_and_sources(self):
        d = summary.draft(SCENARIOS["ear"]["outcome"])
        self.assertEqual(d["footer"], "Questions? Contact your clinic.")
        notes = SCENARIOS["ear"]["outcome"]["notes"]
        for item in d["next_steps"] + d["warning_signs"]:
            self.assertTrue(item["source"] in notes or item["source"] == SCENARIOS["ear"]["outcome"]["rx_generic"], item)
        self.assertTrue(any("three times a day" in i["text"] for i in d["next_steps"]))

    def test_ai_lines_without_a_real_quote_are_dropped(self):
        fake = {"diagnosis_title": "Sinus infection",
                "what_you_have": {"text": "You have a sinus infection.", "source": "Acute Sinusitis & Right Otitis Media"},
                "what_we_found": [],
                "next_steps": [{"text": "Take amoxicillin 3x a day for 10 days.", "source": "Start Amoxicillin 500mg PO TID x10d"},
                               {"text": "Take vitamin C daily.", "source": "Vitamin C 1000mg daily"}],
                "warning_signs": [{"text": "Fever over 102F.", "source": "Return if temp >102F"}]}
        with mock.patch.object(ai, "ask_json", return_value=fake):
            d = summary.draft(SCENARIOS["ear"]["outcome"])
        self.assertEqual(d["generated_by"], "claude")
        self.assertEqual([i["text"] for i in d["next_steps"]], ["Take amoxicillin 3x a day for 10 days."])
        self.assertEqual(len(d["dropped_ungrounded"]), 1)


class QA(unittest.TestCase):
    def setUp(self):
        self.s = summary.draft(SCENARIOS["ear"]["outcome"])

    def test_answers_from_summary(self):
        r = qa.answer("How many times a day do I take the antibiotic?", self.s)
        self.assertEqual(r["kind"], "answer")
        self.assertIn("three times a day", r["answer"])
        self.assertIn("Questions? Contact your clinic.", r["answer"])

    def test_escalates_unknowns(self):
        for q in ("Can I drink alcohol with this?", "Can I go back to work tomorrow?"):
            r = qa.answer(q, self.s)
            self.assertTrue(r["escalated"], q)
            self.assertIn("care team", r["answer"])

    def test_emergency_question(self):
        self.assertEqual(qa.answer("I'm having chest pain right now", self.s)["kind"], "emergency")

    def test_ai_answer_needs_real_quote(self):
        with mock.patch.object(ai, "ask_json", return_value={"answerable": True, "answer": "Yes, alcohol is fine.", "quote": "Alcohol is fine"}):
            r = qa.answer("When should I call?", self.s)
        self.assertTrue(r["escalated"])


class Auth(unittest.TestCase):
    def test_login_and_tamper(self):
        self.assertIsNone(auth.login("dr.demo", "wrong"))
        t = auth.login("dr.demo", auth._DEMO_PASSWORD)["token"]
        self.assertEqual(auth.verify("Bearer " + t)["role"], "doctor")
        self.assertIsNone(auth.verify("Bearer " + t[:-2] + "00"))
        self.assertIsNone(auth.verify(None))


class StoreFlow(unittest.TestCase):
    def test_full_flow_and_approval_gate(self):
        v = store.create_visit(SCENARIOS["ear"]["intake"], "ear")
        store.set_outcome(v["id"], SCENARIOS["ear"]["outcome"])
        pv = store.patient_view(v)
        self.assertIsNone(pv["summary"])                     # draft is never shown to the patient
        self.assertEqual(pv["summary_status"], "awaiting_approval")
        with self.assertRaises(ValueError):
            store.ask(v["id"], "When do I take it?")
        store.approve_summary(v["id"], None, {"name": "Dr. Test"})
        pv = store.patient_view(v)
        self.assertEqual(pv["summary"]["footer"], "Questions? Contact your clinic.")
        self.assertEqual(pv["billing"]["total_patient"], 41.8)
        q = store.ask(v["id"], "Can I drink alcohol with this?")
        self.assertTrue(q["escalated"])
        self.assertTrue(any(x["id"] == q["id"] for x in store.inbox()["questions"]))

    def test_emergency_visit_skips_prep_and_alerts_red(self):
        v = store.create_visit(SCENARIOS["chest"]["intake"], "chest")
        self.assertIsNone(v["patient_prep"])
        self.assertEqual(v["alerts"][0]["level"], "red")
        self.assertEqual(v["brief"]["agenda"][0]["priority"], "urgent")


class FollowUpAgent(unittest.TestCase):
    DOC = {"name": "Dr. Demo (Test Clinician)"}

    def approved_ear_visit(self):
        v = store.create_visit(SCENARIOS["ear"]["intake"], scenario="ear")
        store.set_outcome(v["id"], SCENARIOS["ear"]["outcome"], use_ai=False)
        store.approve_summary(v["id"], None, self.DOC)
        return v

    def test_day0_text_on_approval_and_day3_question_matches_symptom(self):
        v = self.approved_ear_visit()
        f = v["followup"]
        self.assertEqual(f["stage"], "scheduled")
        self.assertIn("check in with you in 3 days", f["messages"][0]["text"])
        store.send_checkin(v["id"])
        self.assertIn("Is your ear feeling better?", f["messages"][-1]["text"])
        self.assertEqual(f["messages"][-1]["day"], 3)
        self.assertEqual(f["stage"], "awaiting_checkin")

    def test_no_followup_before_approval(self):
        v = store.create_visit(SCENARIOS["ear"]["intake"])
        self.assertIsNone(v["followup"])
        with self.assertRaises(ValueError):
            store.followup_reply(v["id"], "hi")

    def test_due_checkins_send_themselves(self):
        v = self.approved_ear_visit()
        v["followup"]["due_at"] = "2000-01-01T00:00:00+00:00"
        store.send_due_followups()
        self.assertIsNotNone(v["followup"]["checkin_sent_at"])

    def test_better_then_nothing_needed_stays_out_of_inbox(self):
        v = self.approved_ear_visit()
        store.send_checkin(v["id"])
        store.followup_reply(v["id"], "Yes, much better and no fever")
        self.assertIn("Do you need anything", v["followup"]["messages"][-1]["text"])
        store.followup_reply(v["id"], "No, I'm good")
        self.assertEqual(v["followup"]["stage"], "done")
        self.assertEqual(v["followup_flags"], [])

    def test_red_flag_reply_gets_911_and_red_inbox_item(self):
        v = self.approved_ear_visit()
        store.send_checkin(v["id"])
        store.followup_reply(v["id"], "I have chest pain now")
        self.assertIn("911", v["followup"]["messages"][-1]["text"])
        mine = [f for f in store.inbox()["followups"] if f["visit_id"] == v["id"]]
        self.assertEqual(mine[0]["level"], "red")
        self.assertIn("RED FLAG", mine[0]["reason"])

    def test_crisis_line_on_self_harm_reply(self):
        r = followup.handle_reply("I want to kill myself", "awaiting_checkin", None, "en")
        self.assertIn("988", r["replies"][0])

    def test_not_better_request_and_unclear_go_to_staff(self):
        for msg, level in [("No", "amber"), ("Still hurts and the fever is back", "amber"), ("Can I get a work note?", "request"),
                           ("banana", "amber")]:
            r = followup.handle_reply(msg, "awaiting_checkin", None, "en")
            self.assertEqual(r["flag"]["level"], level, msg)

    def test_staff_reply_reaches_patient_thread(self):
        v = self.approved_ear_visit()
        store.send_checkin(v["id"])
        store.followup_reply(v["id"], "I need a refill please")
        fl = v["followup_flags"][-1]
        store.resolve_followup(v["id"], fl["id"], "Sent to your pharmacy.", self.DOC)
        self.assertEqual(fl["status"], "resolved")
        last = store.patient_view(v)["followup"]["messages"][-1]
        self.assertEqual((last["from"], last["text"]), ("care_team", "Sent to your pharmacy."))
        self.assertNotIn("followup_flags", store.patient_view(v))

    def test_spanish(self):
        self.assertEqual(followup.checkin_question([{"id": "ear"}], "", "es"), "¿Se siente mejor su oído?")
        self.assertIsNone(followup.handle_reply("Sí, mucho mejor", "awaiting_checkin", None, "es")["flag"])


class Fhir(unittest.TestCase):
    def test_bundle(self):
        v = store.create_visit(SCENARIOS["bp"]["intake"], "bp")
        store.set_outcome(v["id"], SCENARIOS["bp"]["outcome"])
        store.approve_summary(v["id"], None, {"name": "Dr. Test"})
        b = fhir_export.bundle(v)
        types = [e["resource"]["resourceType"] for e in b["entry"]]
        for t in ("Patient", "Encounter", "QuestionnaireResponse", "AllergyIntolerance", "MedicationStatement",
                  "Condition", "MedicationRequest", "DocumentReference"):
            self.assertIn(t, types)
        self.assertTrue(all(e["fullUrl"].startswith("urn:uuid:") for e in b["entry"]))
        self.assertIn("SYNTHETIC", fhir_export.note_text(v))


class Savings(unittest.TestCase):
    def test_defaults_pay_for_themselves(self):
        r = savings.calculate({})
        self.assertTrue(r["pays_for_itself"])
        self.assertEqual(len(r["metrics"]), 3)
        self.assertIn("estimate", r["disclaimer"].lower())

    def test_inputs_are_clamped(self):
        self.assertEqual(savings.calculate({"patients_per_day": -5})["inputs"]["patients_per_day"], 1)


class Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server
        cls.httpd = server.make_server(port=0)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def call(self, method, path, body=None, token=None):
        req = urllib.request.Request(self.base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + token} if token else {})})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_end_to_end(self):
        self.assertEqual(self.call("GET", "/api/health")[0], 200)
        self.assertEqual(self.call("GET", "/api/staff/queue")[0], 401)
        code, v = self.call("POST", "/api/intake", SCENARIOS["ankle"]["intake"])
        self.assertEqual(code, 200)
        vid = v["visit_id"]
        nurse = self.call("POST", "/api/login", {"username": "nurse.demo", "password": auth._DEMO_PASSWORD})[1]["token"]
        doc = self.call("POST", "/api/login", {"username": "dr.demo", "password": auth._DEMO_PASSWORD})[1]["token"]
        self.assertEqual(self.call("POST", f"/api/staff/visits/{vid}/outcome", SCENARIOS["ankle"]["outcome"], nurse)[0], 200)
        self.assertEqual(self.call("POST", f"/api/staff/visits/{vid}/approve", {}, nurse)[0], 403)   # nurses can't approve
        self.assertEqual(self.call("POST", f"/api/staff/visits/{vid}/approve", {}, doc)[0], 200)
        code, pv = self.call("GET", f"/api/patient/visits/{vid}?generic=0")
        self.assertEqual(pv["summary_status"], "approved")
        self.assertFalse(pv["billing"]["use_generic"])
        code, exp = self.call("GET", f"/api/staff/visits/{vid}/export", token=nurse)
        self.assertEqual(exp["fhir"]["resourceType"], "Bundle")
        code, q = self.call("POST", f"/api/patient/visits/{vid}/ask", {"question": "How often do I ice it?"})
        self.assertEqual(code, 200)
        code, pv = self.call("POST", f"/api/patient/visits/{vid}/followup/send-now", {})
        self.assertIn("Is your ankle feeling better?", pv["followup"]["messages"][-1]["text"])
        code, pv = self.call("POST", f"/api/patient/visits/{vid}/followup", {"message": "It's still swollen and worse"})
        self.assertEqual(code, 200)
        inbox = self.call("GET", "/api/staff/inbox", token=nurse)[1]
        fl = next(f for f in inbox["followups"] if f["visit_id"] == vid)
        code, _ = self.call("POST", f"/api/staff/visits/{vid}/followups/{fl['id']}/resolve", {"reply": "Nurse will call at 2pm."}, nurse)
        self.assertEqual(code, 200)
        pv = self.call("GET", f"/api/patient/visits/{vid}")[1]
        self.assertEqual(pv["followup"]["messages"][-1]["text"], "Nurse will call at 2pm.")
        code, s = self.call("POST", "/api/savings", {"patients_per_day": 40})
        self.assertTrue(s["pays_for_itself"])

    def test_red_flag_over_http(self):
        code, v = self.call("POST", "/api/intake", SCENARIOS["chest"]["intake"])
        self.assertEqual(v["safety"]["level"], "emergency")
        self.assertIsNone(v["patient_prep"])


if __name__ == "__main__":
    unittest.main()
