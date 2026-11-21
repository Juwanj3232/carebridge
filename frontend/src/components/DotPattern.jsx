import { useId } from 'react';

// Background dot grid, after Magic UI's DotPattern (same props: width, height, x, y, cx, cy, cr, className).
// It draws one repeating SVG tile instead of one <circle> per dot, so it costs the same on any screen size.
// The glow animation is left out on purpose: thousands of moving dots behind medical text would distract.
export default function DotPattern({ width = 16, height = 16, x = 0, y = 0, cx = 1, cy = 1, cr = 1, className = '', ...props }) {
  const id = useId();
  return (
    <svg aria-hidden="true" className={`pointer-events-none absolute inset-0 h-full w-full ${className}`} {...props}>
      <defs>
        <pattern id={`${id}-dots`} width={width} height={height} x={x} y={y} patternUnits="userSpaceOnUse">
          <circle cx={cx} cy={cy} r={cr} fill="currentColor" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id}-dots)`} />
    </svg>
  );
}
