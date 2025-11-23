import { useEffect, useRef } from 'react'

export default function AntigravityBackground() {
    const canvasRef = useRef(null)

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return

        const ctx = canvas.getContext('2d')
        if (!ctx) return

        // Set canvas size
        const resizeCanvas = () => {
            canvas.width = window.innerWidth
            canvas.height = window.innerHeight
        }
        resizeCanvas()
        window.addEventListener('resize', resizeCanvas)

        // Animation variables
        let time = 0
        let mouseX = 0
        let mouseY = 0

        // Mouse tracking
        const handleMouseMove = (e) => {
            mouseX = e.clientX / window.innerWidth
            mouseY = e.clientY / window.innerHeight
        }
        window.addEventListener('mousemove', handleMouseMove)

        // Simplex-like noise function (simplified)
        const noise = (x, y, t) => {
            return Math.sin(x * 0.01 + t) * Math.cos(y * 0.01 + t * 0.5) * 0.5 + 0.5
        }

        // Animation loop
        const animate = () => {
            time += 0.002 // Slow movement

            // Create gradient base
            const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
            gradient.addColorStop(0, '#0a0a0a')
            gradient.addColorStop(0.5, '#1a1a1a')
            gradient.addColorStop(1, '#0a0a0a')

            ctx.fillStyle = gradient
            ctx.fillRect(0, 0, canvas.width, canvas.height)

            // Draw fluid distortion effect
            const gridSize = 40
            ctx.strokeStyle = 'rgba(200, 200, 190, 0.03)'
            ctx.lineWidth = 1

            for (let x = 0; x < canvas.width; x += gridSize) {
                for (let y = 0; y < canvas.height; y += gridSize) {
                    const n = noise(x + mouseX * 100, y + mouseY * 100, time)
                    const offsetX = Math.sin(n * Math.PI * 2) * 20
                    const offsetY = Math.cos(n * Math.PI * 2) * 20

                    ctx.beginPath()
                    ctx.arc(x + offsetX, y + offsetY, 2, 0, Math.PI * 2)
                    ctx.fill()
                }
            }

            // Add subtle glow spots
            const spots = 5
            for (let i = 0; i < spots; i++) {
                const spotX = (Math.sin(time * 0.5 + i) * 0.5 + 0.5) * canvas.width
                const spotY = (Math.cos(time * 0.3 + i) * 0.5 + 0.5) * canvas.height

                const spotGradient = ctx.createRadialGradient(spotX, spotY, 0, spotX, spotY, 200)
                spotGradient.addColorStop(0, 'rgba(200, 200, 190, 0.05)')
                spotGradient.addColorStop(1, 'rgba(200, 200, 190, 0)')

                ctx.fillStyle = spotGradient
                ctx.fillRect(0, 0, canvas.width, canvas.height)
            }

            requestAnimationFrame(animate)
        }

        animate()

        return () => {
            window.removeEventListener('resize', resizeCanvas)
            window.removeEventListener('mousemove', handleMouseMove)
        }
    }, [])

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            zIndex: -1,
            background: '#0a0a0a'
        }}>
            <canvas
                ref={canvasRef}
                style={{
                    width: '100%',
                    height: '100%',
                    display: 'block'
                }}
            />
        </div>
    )
}
