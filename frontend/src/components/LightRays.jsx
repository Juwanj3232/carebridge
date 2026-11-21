import { useEffect, useState } from 'react';

// Animated light rays shining down from the top, after Magic UI's LightRays (same props: count, color, blur, speed,
// length). Ported to plain React + CSS keyframes (index.css: .light-ray), so it needs no animation library.
// The color defaults to the theme's --light-rays-color (red on white, brighter red on black).
// People who ask their device for reduced motion get still rays.

function createRays(count, cycle) {
  if (count <= 0) return [];
  return Array.from({ length: count }, (_, index) => {
    const left = 8 + Math.random() * 84;
    const rotate = -28 + Math.random() * 56;
    const width = 160 + Math.random() * 160;
    const swing = 0.8 + Math.random() * 1.8;
    const delay = Math.random() * cycle;
    const duration = cycle * (0.75 + Math.random() * 0.5);
    const intensity = 0.6 + Math.random() * 0.5;
    return { id: `${index}-${Math.round(left * 10)}`, left, rotate, width, swing, delay, duration, intensity };
  });
}

function Ray({ left, rotate, width, swing, delay, duration, intensity }) {
  return (
    <div
      className="light-ray"
      style={{
        '--ray-left': `${left}%`,
        '--ray-width': `${width}px`,
        '--ray-rotate': `${rotate}deg`,
        '--ray-swing': `${swing}deg`,
        '--ray-intensity': intensity,
        // repeatDelay in the original: the ray rests (invisible) for the last tenth of each cycle.
        animationDuration: `${duration * 1.1}s`,
        animationDelay: `${delay}s`,
      }}
    />
  );
}

export default function LightRays({ className = '', style, count = 7, color, blur = 36, speed = 14, length = '70vh', ...props }) {
  const [rays, setRays] = useState([]);
  const cycle = Math.max(speed, 0.1);

  useEffect(() => { setRays(createRays(count, cycle)); }, [count, cycle]);

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 isolate overflow-hidden rounded-[inherit] ${className}`}
      style={{
        ...(color ? { '--light-rays-color': color } : {}),
        '--light-rays-blur': `${blur}px`,
        '--light-rays-length': typeof length === 'number' ? `${length}px` : length,
        ...style,
      }}
      {...props}
    >
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 opacity-60"
          style={{ background: 'radial-gradient(circle at 20% 15%, color-mix(in srgb, var(--light-rays-color) 45%, transparent), transparent 70%)' }} />
        <div className="absolute inset-0 opacity-60"
          style={{ background: 'radial-gradient(circle at 80% 10%, color-mix(in srgb, var(--light-rays-color) 35%, transparent), transparent 75%)' }} />
        {rays.map((ray) => <Ray key={ray.id} {...ray} />)}
      </div>
    </div>
  );
}
