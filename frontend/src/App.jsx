import { useState, useEffect } from 'react'
import { io } from 'socket.io-client'
import { motion, AnimatePresence } from 'framer-motion'
import AntigravityBackground from './components/AntigravityBackground'
import './index.css'

function App() {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [aiInsights, setAiInsights] = useState(null)
  const [sensorData, setSensorData] = useState({
    moisture: '0',
    temperature: '0',
    ph: '--',
    waterLevel: '--',
    pumpStatus: 'OFF'
  })

  useEffect(() => {
    const socketInstance = io('http://localhost:5000', {
      transports: ['websocket', 'polling']
    })

    socketInstance.on('connect', () => {
      console.log('Connected to backend')
      setConnected(true)
    })

    socketInstance.on('disconnect', () => {
      console.log('Disconnected from backend')
      setConnected(false)
    })

    socketInstance.on('sensor_data', (data) => {
      setSensorData({
        moisture: data.moisture?.toFixed(1) || '0',
        temperature: data.temperature?.toFixed(1) || '0',
        ph: data.ph?.toFixed(1) || '0',
        waterLevel: data.water_level?.toFixed(0) || '0'
      })
    })

    socketInstance.on('actuator_command', (data) => {
      if (data.pump !== undefined) {
        setSensorData(prev => ({
          ...prev,
          pumpStatus: data.pump === 1 ? 'ON' : 'OFF'
        }))
      }
    })

    socketInstance.on('fog_status', (data) => {
      console.log('Fog status:', data)
    })

    setSocket(socketInstance)

    return () => {
      socketInstance.disconnect()
    }
  }, [])

  // Fetch AI insights
  useEffect(() => {
    const fetchAIInsights = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/ai-insights')
        const data = await response.json()
        setAiInsights(data)
      } catch (error) {
        console.error('Failed to fetch AI insights:', error)
      }
    }

    fetchAIInsights()
    const interval = setInterval(fetchAIInsights, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [])

  const glassCardStyle = {
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(24px)',
    WebkitBackdropFilter: 'blur(24px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '20px',
    padding: '24px',
    transition: 'all 0.3s ease'
  }

  const sidebarStyle = {
    position: 'fixed',
    left: sidebarOpen ? '0' : '-240px',
    top: '0',
    height: '100vh',
    width: '260px',
    background: 'rgba(10, 10, 15, 0.8)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderLeft: 'none',
    padding: '30px 20px',
    transition: 'left 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
    zIndex: 1000,
    boxShadow: '4px 0 24px rgba(0, 0, 0, 0.5)'
  }

  const toggleButtonStyle = {
    position: 'fixed',
    left: sidebarOpen ? '260px' : '0px',
    top: '30px',
    zIndex: 1001,
    background: 'rgba(0, 212, 255, 0.2)',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    border: '1px solid rgba(0, 212, 255, 0.4)',
    borderRadius: '0 12px 12px 0',
    padding: '12px 16px',
    color: '#00d4ff',
    cursor: 'pointer',
    fontSize: '20px',
    transition: 'all 0.3s ease',
    fontWeight: 'bold'
  }

  return (
    <div style={{ minHeight: '100vh', color: '#fff', position: 'relative' }}>
      <AntigravityBackground key="fluid-effect" />

      {/* Sidebar Toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        style={toggleButtonStyle}
        onMouseOver={(e) => {
          e.currentTarget.style.background = 'rgba(0, 212, 255, 0.3)'
          e.currentTarget.style.transform = 'scale(1.05)'
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.background = 'rgba(0, 212, 255, 0.2)'
          e.currentTarget.style.transform = 'scale(1)'
        }}
      >
        {sidebarOpen ? '◀' : '▶'}
      </button>

      {/* Sidebar */}
      <div style={sidebarStyle}>
        <div style={{ marginBottom: '40px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '30px' }}>
            <div style={{ fontSize: '36px' }}>🌱</div>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: '800', margin: '0', background: 'linear-gradient(135deg, #00d4ff, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                smart agriculture
              </h1>
            </div>
          </div>

          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            background: connected ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${connected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '20px',
            fontSize: '12px',
            fontFamily: 'JetBrains Mono, monospace'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: connected ? '#10b981' : '#ef4444',
              animation: 'pulse 2s infinite'
            }} />
            {connected ? 'ONLINE' : 'OFFLINE'}
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {[
            { icon: '📊', label: 'Dashboard', id: 'dashboard' },
            { icon: '🤖', label: 'AI Models', id: 'ai' },
            { icon: '📈', label: 'Analytics', id: 'analytics' },
            { icon: '⚙️', label: 'Settings', id: 'settings' }
          ].map((item, i) => (
            <button
              key={i}
              onClick={() => {
                setActiveTab(item.id)
                console.log(`Navigating to: ${item.label}`)
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 16px',
                background: activeTab === item.id ? 'rgba(255,255,255,0.1)' : 'transparent',
                border: 'none',
                borderRadius: '12px',
                color: activeTab === item.id ? '#fff' : 'rgba(255,255,255,0.6)',
                fontSize: '14px',
                fontFamily: 'JetBrains Mono, monospace',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.08)'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = activeTab === item.id ? 'rgba(255,255,255,0.1)' : 'transparent'
              }}
            >
              <span style={{ fontSize: '18px' }}>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <main style={{
        marginLeft: sidebarOpen ? '280px' : '20px',
        padding: '30px',
        transition: 'margin-left 0.4s ease',
        position: 'relative',
        zIndex: 10
      }}>
        {/* Conditional Content Based on Active Tab */}
        {activeTab === 'dashboard' && (
          <>
            {/* Header */}
            <div style={glassCardStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ fontSize: '28px', fontWeight: '700', margin: '0' }}>Live Monitoring</h2>
                <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {new Date().toLocaleTimeString()}
                </div>
              </div>
            </div>

            {/* Metrics Grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '20px',
              marginTop: '30px'
            }}>
              {[
                { title: 'SOIL MOISTURE', value: sensorData.moisture, unit: '%', icon: '💧', color: '#00d4ff', gradient: 'linear-gradient(135deg, #00d4ff, #3b82f6)' },
                { title: 'TEMPERATURE', value: sensorData.temperature, unit: '°C', icon: '🌡️', color: '#fb923c', gradient: 'linear-gradient(135deg, #fb923c, #ef4444)' },
                { title: 'pH LEVEL', value: sensorData.ph, unit: '', icon: '⚗️', color: '#a78bfa', gradient: 'linear-gradient(135deg, #a78bfa, #9333ea)' },
                { title: 'WATER TANK', value: sensorData.waterLevel, unit: '%', icon: '🚰', color: '#10b981', gradient: 'linear-gradient(135deg, #10b981, #059669)' }
              ].map((metric, i) => (
                <motion.div
                  key={i}
                  style={{
                    ...glassCardStyle,
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                  whileHover={{ scale: 1.03, borderColor: 'rgba(255,255,255,0.25)' }}
                  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <div style={{
                      fontSize: '11px',
                      fontWeight: '600',
                      color: 'rgba(255,255,255,0.5)',
                      letterSpacing: '1px',
                      fontFamily: 'JetBrains Mono, monospace'
                    }}>
                      {metric.title}
                    </div>
                    <div style={{ fontSize: '28px' }}>{metric.icon}</div>
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <span style={{
                      fontSize: '56px',
                      fontWeight: '800',
                      background: metric.gradient,
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      lineHeight: '1'
                    }}>
                      {metric.value}
                    </span>
                    {metric.unit && (
                      <span style={{ fontSize: '24px', color: 'rgba(255,255,255,0.4)', marginLeft: '8px' }}>
                        {metric.unit}
                      </span>
                    )}
                  </div>

                  <div style={{
                    height: '4px',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <motion.div
                      style={{
                        height: '100%',
                        background: metric.gradient,
                        borderRadius: '4px'
                      }}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(parseFloat(metric.value) || 0, 100)}%` }}
                      transition={{ duration: 1, ease: 'easeOut' }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Additional Info Row */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '20px',
              marginTop: '30px'
            }}>
              <div style={glassCardStyle}>
                <div style={{
                  fontSize: '11px',
                  fontWeight: '600',
                  color: 'rgba(255,255,255,0.5)',
                  letterSpacing: '1px',
                  fontFamily: 'JetBrains Mono, monospace',
                  marginBottom: '20px'
                }}>
                  PUMP STATUS
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                  <div style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '16px',
                    background: sensorData.pumpStatus === 'ON' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '32px'
                  }}>
                    ⚙️
                  </div>
                  <div>
                    <div style={{ fontSize: '32px', fontWeight: '700', marginBottom: '4px' }}>
                      {sensorData.pumpStatus}
                    </div>
                    <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                      Irrigation System
                    </div>
                  </div>
                </div>
              </div>

              <div style={glassCardStyle}>
                <div style={{
                  fontSize: '11px',
                  fontWeight: '600',
                  color: 'rgba(255,255,255,0.5)',
                  letterSpacing: '1px',
                  fontFamily: 'JetBrains Mono, monospace',
                  marginBottom: '20px'
                }}>
                  AI INTELLIGENCE
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {[
                    { label: 'Active Model', value: aiInsights?.model_info?.active_model || 'Random Forest', color: '#a78bfa' },
                    { label: 'Accuracy', value: aiInsights?.model_info?.accuracy || '98.2%', color: '#00d4ff' },
                    { label: 'Predictions', value: aiInsights?.model_info?.total_predictions || '1,523', color: '#fff' }
                  ].map((item, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)' }}>{item.label}</span>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', color: item.color, fontWeight: '600' }}>
                        {item.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* AI Predictions Section */}
            {aiInsights && (
              <div style={{ ...glassCardStyle, marginTop: '30px' }}>
                <div style={{
                  fontSize: '11px',
                  fontWeight: '600',
                  color: 'rgba(255,255,255,0.5)',
                  letterSpacing: '1px',
                  fontFamily: 'JetBrains Mono, monospace',
                  marginBottom: '20px'
                }}>
                  🤖 AI PREDICTIONS & INSIGHTS
                </div>

                <div style={{ display: 'grid', gap: '16px' }}>
                  {/* Prediction */}
                  {aiInsights.prediction && (
                    <div style={{ padding: '16px', background: 'rgba(0, 212, 255, 0.05)', borderRadius: '12px', border: '1px solid rgba(0, 212, 255, 0.2)' }}>
                      <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)', marginBottom: '8px' }}>Next Irrigation Prediction</div>
                      <div style={{ fontSize: '24px', fontWeight: '700', color: '#00d4ff' }}>
                        {aiInsights.prediction.action === 'irrigate' ? '💧 Irrigate' : '⏸️ Hold'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', marginTop: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
                        Confidence: {(aiInsights.prediction.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {aiInsights.recommendations && aiInsights.recommendations.length > 0 && (
                    <div>
                      <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.7)', marginBottom: '12px', fontWeight: '600' }}>Recommendations</div>
                      {aiInsights.recommendations.map((rec, i) => (
                        <div key={i} style={{
                          padding: '12px',
                          background: 'rgba(255,255,255,0.02)',
                          borderRadius: '8px',
                          marginBottom: '8px',
                          borderLeft: '3px solid #a78bfa'
                        }}>
                          <div style={{ fontSize: '13px', color: '#fff' }}>{rec.message}</div>
                          <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginTop: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
                            Priority: {rec.priority}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Insights */}
                  {aiInsights.insights && (
                    <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.05)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)' }}>
                        {aiInsights.insights}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {/* AI Models Section */}
        {activeTab === 'ai' && (
          <>
            <div style={glassCardStyle}>
              <h2 style={{ fontSize: '28px', fontWeight: '700', margin: '0 0 8px 0' }}>🤖 AI Models</h2>
              <p style={{ color: 'rgba(255,255,255,0.6)', margin: '0' }}>Machine learning models for predictive agriculture</p>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '20px',
              marginTop: '30px'
            }}>
              {[
                {
                  name: 'Random Forest',
                  status: 'ACTIVE',
                  accuracy: '98.2%',
                  predictions: '1,523',
                  type: 'Regression',
                  icon: '🌲',
                  color: '#10b981'
                },
                {
                  name: 'Gradient Boosting',
                  status: 'STANDBY',
                  accuracy: '97.8%',
                  predictions: '1,523',
                  type: 'Regression',
                  icon: '📈',
                  color: '#a78bfa'
                },
                {
                  name: 'Linear Regression',
                  status: 'STANDBY',
                  accuracy: '87.3%',
                  predictions: '1,523',
                  type: 'Baseline',
                  icon: '📊',
                  color: '#00d4ff'
                }
              ].map((model, i) => (
                <motion.div
                  key={i}
                  style={glassCardStyle}
                  whileHover={{ scale: 1.02 }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ fontSize: '32px' }}>{model.icon}</div>
                      <div>
                        <h3 style={{ margin: '0', fontSize: '18px', fontWeight: '700' }}>{model.name}</h3>
                        <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', fontFamily: 'JetBrains Mono, monospace' }}>
                          {model.type}
                        </span>
                      </div>
                    </div>
                    <div style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '10px',
                      fontWeight: '600',
                      fontFamily: 'JetBrains Mono, monospace',
                      background: model.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.05)',
                      color: model.status === 'ACTIVE' ? '#10b981' : 'rgba(255,255,255,0.5)',
                      border: `1px solid ${model.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255,255,255,0.1)'}`
                    }}>
                      {model.status}
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {[
                      { label: 'Accuracy', value: model.accuracy },
                      { label: 'Total Predictions', value: model.predictions }
                    ].map((stat, j) => (
                      <div key={j} style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)' }}>{stat.label}</span>
                        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: '600', color: model.color }}>
                          {stat.value}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>

            <div style={{ ...glassCardStyle, marginTop: '30px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', margin: '0 0 16px 0' }}>Training History</h3>
              <div style={{ color: 'rgba(255,255,255,0.6)', fontFamily: 'JetBrains Mono, monospace', fontSize: '13px' }}>
                <div>✅ Last training: 2 hours ago</div>
                <div style={{ marginTop: '8px' }}>📊 Dataset size: 10,250 samples</div>
                <div style={{ marginTop: '8px' }}>🎯 Cross-validation: 5-fold</div>
              </div>
            </div>
          </>
        )}

        {/* Analytics Section */}
        {activeTab === 'analytics' && (
          <>
            <div style={glassCardStyle}>
              <h2 style={{ fontSize: '28px', fontWeight: '700', margin: '0 0 8px 0' }}>📈 Analytics</h2>
              <p style={{ color: 'rgba(255,255,255,0.6)', margin: '0' }}>System performance and insights</p>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '20px',
              marginTop: '30px'
            }}>
              {[
                { title: 'Total Predictions', value: '1,523', icon: '🎯', gradient: 'linear-gradient(135deg, #00d4ff, #3b82f6)' },
                { title: 'Uptime', value: '99.8%', icon: '⏱️', gradient: 'linear-gradient(135deg, #10b981, #059669)' },
                { title: 'Avg Response', value: '42ms', icon: '⚡', gradient: 'linear-gradient(135deg, #fb923c, #ef4444)' },
                { title: 'Data Points', value: '10.2K', icon: '📊', gradient: 'linear-gradient(135deg, #a78bfa, #9333ea)' }
              ].map((stat, i) => (
                <motion.div
                  key={i}
                  style={glassCardStyle}
                  whileHover={{ scale: 1.03 }}
                >
                  <div style={{ fontSize: '32px', marginBottom: '12px' }}>{stat.icon}</div>
                  <div style={{
                    fontSize: '36px',
                    fontWeight: '800',
                    background: stat.gradient,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    marginBottom: '8px'
                  }}>
                    {stat.value}
                  </div>
                  <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', fontFamily: 'JetBrains Mono, monospace' }}>
                    {stat.title}
                  </div>
                </motion.div>
              ))}
            </div>

            <div style={{ ...glassCardStyle, marginTop: '30px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', margin: '0 0 20px 0' }}>Recent Activity</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {[
                  { time: '2m ago', action: 'Irrigation activated', icon: '💧', color: '#00d4ff' },
                  { time: '15m ago', action: 'Model prediction completed', icon: '🤖', color: '#a78bfa' },
                  { time: '1h ago', action: 'pH level adjusted', icon: '⚗️', color: '#10b981' },
                  { time: '2h ago', action: 'System health check passed', icon: '✅', color: '#10b981' }
                ].map((activity, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px' }}>
                    <div style={{ fontSize: '24px' }}>{activity.icon}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '14px', fontWeight: '600' }}>{activity.action}</div>
                      <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', fontFamily: 'JetBrains Mono, monospace', marginTop: '2px' }}>
                        {activity.time}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Settings Section */}
        {activeTab === 'settings' && (
          <>
            <div style={glassCardStyle}>
              <h2 style={{ fontSize: '28px', fontWeight: '700', margin: '0 0 8px 0' }}>⚙️ Settings</h2>
              <p style={{ color: 'rgba(255,255,255,0.6)', margin: '0' }}>Configure system parameters</p>
            </div>

            <div style={{ display: 'grid', gap: '20px', marginTop: '30px' }}>
              {[
                {
                  title: 'System Configuration',
                  settings: [
                    { label: 'MQTT Broker', value: 'localhost:1883', editable: false },
                    { label: 'Update Interval', value: '5 seconds', editable: true },
                    { label: 'Data Retention', value: '30 days', editable: true }
                  ]
                },
                {
                  title: 'ML Model Configuration',
                  settings: [
                    { label: 'Active Model', value: 'Random Forest', editable: true },
                    { label: 'Auto-Retrain', value: 'Enabled', editable: true },
                    { label: 'Prediction Threshold', value: '0.85', editable: true }
                  ]
                },
                {
                  title: 'Irrigation Settings',
                  settings: [
                    { label: 'Auto Mode', value: 'Enabled', editable: true },
                    { label: 'Min Moisture', value: '40%', editable: true },
                    { label: 'Max Duration', value: '30 minutes', editable: true }
                  ]
                }
              ].map((section, i) => (
                <div key={i} style={glassCardStyle}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', margin: '0 0 20px 0', color: '#00d4ff' }}>
                    {section.title}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {section.settings.map((setting, j) => (
                      <div key={j} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px' }}>
                        <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.8)' }}>{setting.label}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '13px', color: setting.editable ? '#a78bfa' : 'rgba(255,255,255,0.6)' }}>
                            {setting.value}
                          </span>
                          {setting.editable && (
                            <button style={{
                              padding: '6px 12px',
                              background: 'rgba(0, 212, 255, 0.2)',
                              border: '1px solid rgba(0, 212, 255, 0.4)',
                              borderRadius: '8px',
                              color: '#00d4ff',
                              fontSize: '11px',
                              cursor: 'pointer',
                              fontFamily: 'JetBrains Mono, monospace'
                            }}>
                              Edit
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default App
