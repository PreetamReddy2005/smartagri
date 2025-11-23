import { motion } from 'framer-motion'

// Liquid Glass Card Component
export function GlassCard({ children, className = '', hover = true }) {
    return (
        <motion.div
            className={`
        relative overflow-hidden rounded-2xl
        bg-glass-bg backdrop-blur-glass
        border border-glass-border
        glass-noise
        ${className}
      `}
            whileHover={hover ? {
                scale: 1.02,
                borderColor: 'rgba(255, 255, 255, 0.2)'
            } : {}}
            transition={{
                type: 'spring',
                stiffness: 300,
                damping: 20
            }}
        >
            {/* Gradient border glow */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
            {children}
        </motion.div>
    )
}

// Sidebar Component
export function GlassSidebar({ isOpen, onToggle, children }) {
    return (
        <motion.aside
            initial={{ x: -300 }}
            animate={{ x: isOpen ? 0 : -240 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed left-0 top-0 h-full z-50"
        >
            <GlassCard className="h-full w-64 m-4 p-6" hover={false}>
                <button
                    onClick={onToggle}
                    className="absolute right-4 top-4 text-white/60 hover:text-white transition-colors"
                >
                    {isOpen ? '←' : '→'}
                </button>
                {children}
            </GlassCard>
        </motion.aside>
    )
}

// Floating Header
export function GlassHeader({ children }) {
    return (
        <header className="sticky top-0 z-40 p-4">
            <GlassCard className="px-6 py-4" hover={false}>
                {children}
            </GlassCard>
        </header>
    )
}

// Metric Card with Value
export function MetricCard({ title, value, unit, icon, color = 'cyan' }) {
    const colorClasses = {
        cyan: 'from-neon-cyan to-blue-400',
        purple: 'from-neon-purple to-purple-400',
        green: 'from-green-400 to-emerald-500',
        orange: 'from-orange-400 to-red-500'
    }

    return (
        <GlassCard className="p-6">
            <div className="flex items-start justify-between mb-4">
                <span className="font-mono text-xs text-white/40 uppercase tracking-wider">
                    {title}
                </span>
                <span className="text-2xl">{icon}</span>
            </div>

            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 200 }}
                className="mb-2"
            >
                <span className={`text-5xl font-bold bg-gradient-to-r ${colorClasses[color]} bg-clip-text text-transparent`}>
                    {value}
                </span>
                {unit && <span className="text-2xl text-white/40 ml-2">{unit}</span>}
            </motion.div>

            {/* Animated progress bar */}
            <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                    className={`h-full bg-gradient-to-r ${colorClasses[color]}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(value, 100)}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                />
            </div>
        </GlassCard>
    )
}

// Status Badge
export function StatusBadge({ status, text }) {
    const colors = {
        online: 'bg-green-500/20 text-green-400 border-green-500/30',
        offline: 'bg-red-500/20 text-red-400 border-red-500/30',
        warning: 'bg-orange-500/20 text-orange-400 border-orange-500/30'
    }

    return (
        <motion.div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border ${colors[status]}`}
            whileHover={{ scale: 1.05 }}
            transition={{ type: 'spring', stiffness: 400 }}
        >
            <motion.div
                className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-green-400' : status === 'offline' ? 'bg-red-400' : 'bg-orange-400'}`}
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
            />
            <span className="font-mono text-sm">{text}</span>
        </motion.div>
    )
}
