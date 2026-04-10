
import React from 'react'
import './LoadingOrb.css'

const MESSAGES = [
  'Analyzing composition…',
  'Detecting objects…',
  'Understanding context…',
  'Generating caption…',
  'Applying attention…',
]

export default function LoadingOrb() {
  const [msgIdx, setMsgIdx] = React.useState(0)

  React.useEffect(() => {
    const id = setInterval(() => {
      setMsgIdx(i => (i + 1) % MESSAGES.length)
    }, 1800)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="loading-orb-wrap">
      <div className="orb-container">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
        <div className="orb-core">
          <span className="orb-emoji">🤖</span>
        </div>
      </div>
      <p className="loading-msg">{MESSAGES[msgIdx]}</p>
      <div className="loading-dots">
        <span /><span /><span />
      </div>
    </div>
  )
}
