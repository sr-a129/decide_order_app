
'use client'

import { useState } from 'react'

export default function Home() {
  const [fileName, setFileName] = useState('')
  const [matches, setMatches] = useState<any[]>([])
  const [redTeam, setRedTeam] = useState<string[]>([])
  const [whiteTeam, setWhiteTeam] = useState<string[]>([])

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (e.target.files?.[0]) {
      setFileName(e.target.files[0].name)
    }
  }

  const generateMatches = async () => {
    const input = document.getElementById(
      'csvInput'
    ) as HTMLInputElement

    if (!input.files?.[0]) {
      alert('CSVを選択してください')
      return
    }

    const formData = new FormData()
    formData.append('file', input.files[0])

    const res = await fetch(
      'http://localhost:8000/generate?court_count=3',
      {
        method: 'POST',
        body: formData
      }
    )

    const data = await res.json()

    setMatches(data.matches)
    setRedTeam(data.red_team)
    setWhiteTeam(data.white_team)
  }

  return (
    <main style={{ padding: 24 }}>
      <h1>Tennis Match Manager</h1>

      <div style={{ marginBottom: 20 }}>
        <input
          id="csvInput"
          type="file"
          accept=".csv"
          onChange={handleFileChange}
        />

        <button
          onClick={generateMatches}
          style={{ marginLeft: 10 }}
        >
          Generate
        </button>
      </div>

      <p>
        Selected File: {fileName}
      </p>

      <div style={{ display: 'flex', gap: 40 }}>
        <div>
          <h2>Red Team</h2>

          {redTeam.map((p, idx) => (
            <div key={idx}>{p}</div>
          ))}
        </div>

        <div>
          <h2>White Team</h2>

          {whiteTeam.map((p, idx) => (
            <div key={idx}>{p}</div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 30 }}>
        {matches.map((match, idx) => (
          <div
            key={idx}
            style={{
              border: '1px solid #ccc',
              padding: 16,
              marginBottom: 12,
              borderRadius: 8
            }}
          >
            <h2>
              Round {match.round} - Court {match.court}
            </h2>

            <p>
              {match.pair1.join(' / ')}
            </p>

            <p>vs</p>

            <p>
              {match.pair2.join(' / ')}
            </p>

            <p>Status: {match.status}</p>

            <button>Start Match</button>

            <button style={{ marginLeft: 10 }}>
             Finish Match
            </button>
          </div>
        ))}
      </div>
    </main>
  )
}
