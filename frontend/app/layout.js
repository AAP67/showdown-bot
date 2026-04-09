import './globals.css'

export const metadata = {
  title: 'Showdown AI — Pokemon Battle Bot',
  description: 'AI-powered Pokemon Showdown bot with LLM decision making and opponent modeling',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet" />
      </head>
      <body>{children}</body>
    </html>
  )
}
