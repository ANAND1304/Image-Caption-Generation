import { motion } from 'framer-motion';

/**
 * Animated horizontal bar showing model confidence score.
 */
export default function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? 'var(--success)' :
    pct >= 55 ? 'var(--warning)' :
    'var(--accent-bright)';

  return (
    <div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: '0.78rem', color: 'var(--text-muted)',
        marginBottom: '0.4rem', fontWeight: 500,
      }}>
        <span>Model confidence</span>
        <span style={{ color }}>{pct}%</span>
      </div>
      <div style={{
        height: 6, borderRadius: 100,
        background: 'var(--border)',
        overflow: 'hidden',
      }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
          style={{
            height: '100%', borderRadius: 100,
            background: `linear-gradient(90deg, ${color}, ${color}88)`,
          }}
        />
      </div>
    </div>
  );
}
