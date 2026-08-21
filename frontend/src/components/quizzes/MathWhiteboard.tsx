import { useEffect, useRef, useState } from "react"

import "../../styles/components/quizzes/MathWhiteboard.css"

import { Eraser, PenLine, Trash2 } from "lucide-react"


type MathWhiteboardProps = {
  value: string
  onChange: (value: string) => void
}


function MathWhiteboard({
  value,
  onChange,
}: MathWhiteboardProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const hasRestoredRef = useRef(false)
  const [isDrawing, setIsDrawing] = useState(false)
  const [activeTool, setActiveTool] = useState<"pen" | "eraser">("pen")

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

    if (hasRestoredRef.current) {
      return
    }

    hasRestoredRef.current = true

    if (!value) {
      return
    }

    const image = new Image()

    image.onload = () => {
      context.clearRect(0, 0, canvas.width, canvas.height)
      context.globalCompositeOperation = "source-over"
      context.drawImage(image, 0, 0, canvas.width, canvas.height)
    }

    image.src = value
  }, [value])

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

    if (activeTool === "eraser") {
      context.globalCompositeOperation = "destination-out"
      context.lineWidth = 24
    } else {
      context.globalCompositeOperation = "source-over"
      context.strokeStyle = "#1f2937"
      context.lineWidth = 2
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

    const canvas = event.currentTarget
    const context = canvas.getContext("2d")

    context?.closePath()

    if (canvas.hasPointerCapture(event.pointerId)) {
      canvas.releasePointerCapture(event.pointerId)
    }

    setIsDrawing(false)
    onChange(canvas.toDataURL("image/png"))
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

    context.globalCompositeOperation = "source-over"
    context.clearRect(0, 0, canvas.width, canvas.height)
    onChange("")
  }

  return (
    <div className="math-whiteboard">
      <div className="math-whiteboard-header">
        <div>
          <h3>Scratch work</h3>
          <p>Draw your calculations here.</p>
        </div>

        <div className="math-whiteboard-toolbar">
          <div
            className="math-whiteboard-tools"
            role="group"
            aria-label="Drawing tools"
          >
            <button
              type="button"
              className={`math-whiteboard-tool ${activeTool === "pen"
                  ? "math-whiteboard-tool--active"
                  : ""
                }`}
              onClick={() => setActiveTool("pen")}
              aria-label="Pen"
              aria-pressed={activeTool === "pen"}
              title="Pen"
            >
              <PenLine size={16} />
            </button>

            <button
              type="button"
              className={`math-whiteboard-tool ${activeTool === "eraser"
                  ? "math-whiteboard-tool--active"
                  : ""
                }`}
              onClick={() => setActiveTool("eraser")}
              aria-label="Eraser"
              aria-pressed={activeTool === "eraser"}
              title="Eraser"
            >
              <Eraser size={16} />
            </button>
          </div>

          <button
            type="button"
            className="math-whiteboard-clear"
            onClick={clearWhiteboard}
          >
            <Trash2 size={15} />
            Clear
          </button>
        </div>
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