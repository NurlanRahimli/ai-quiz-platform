import { useEffect, useRef, useState } from "react"

import "../../styles/components/quizzes/MathWhiteboard.css"

function MathWhiteboard() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [isDrawing, setIsDrawing] = useState(false)

  useEffect(() => {
    const canvas = canvasRef.current

    if (!canvas) {
      return
    }

    const context = canvas.getContext("2d")

    if (!context) {
      return
    }

    context.lineCap = "round"
    context.lineJoin = "round"
    context.lineWidth = 2
    context.strokeStyle = "#1f2937"
  }, [])

  const getPointerPosition = (
    event: React.PointerEvent<HTMLCanvasElement>,
  ) => {
    const canvas = event.currentTarget
    const rect = canvas.getBoundingClientRect()

    return {
      x: (event.clientX - rect.left) * (canvas.width / rect.width),
      y: (event.clientY - rect.top) * (canvas.height / rect.height),
    }
  }

  const startDrawing = (
    event: React.PointerEvent<HTMLCanvasElement>,
  ) => {
    const context = event.currentTarget.getContext("2d")

    if (!context) {
      return
    }

    const { x, y } = getPointerPosition(event)

    event.currentTarget.setPointerCapture(event.pointerId)

    context.beginPath()
    context.moveTo(x, y)

    setIsDrawing(true)
  }

  const draw = (
    event: React.PointerEvent<HTMLCanvasElement>,
  ) => {
    if (!isDrawing) {
      return
    }

    const context = event.currentTarget.getContext("2d")

    if (!context) {
      return
    }

    const { x, y } = getPointerPosition(event)

    context.lineTo(x, y)
    context.stroke()
  }

  const stopDrawing = (
    event: React.PointerEvent<HTMLCanvasElement>,
  ) => {
    if (!isDrawing) {
      return
    }

    const context = event.currentTarget.getContext("2d")

    context?.closePath()

    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }

    setIsDrawing(false)
  }

  const clearWhiteboard = () => {
    const canvas = canvasRef.current

    if (!canvas) {
      return
    }

    const context = canvas.getContext("2d")

    if (!context) {
      return
    }

    context.clearRect(0, 0, canvas.width, canvas.height)
  }

  return (
    <div className="math-whiteboard">
      <div className="math-whiteboard-header">
        <div>
          <h3>Scratch work</h3>
          <p>Draw your calculations here.</p>
        </div>

        <button
          type="button"
          className="math-whiteboard-clear"
          onClick={clearWhiteboard}
        >
          Clear
        </button>
      </div>

      <canvas
        ref={canvasRef}
        className="math-whiteboard-canvas"
        width={900}
        height={320}
        onPointerDown={startDrawing}
        onPointerMove={draw}
        onPointerUp={stopDrawing}
        onPointerCancel={stopDrawing}
      />
    </div>
  )
}

export default MathWhiteboard