"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { apiClient } from "@/lib/api"
import { ProgressIndicator } from "@/components/progress-indicator"
import { Loader2, Play, Pause, Terminal } from "lucide-react"

interface SSEEvent {
  id: number
  timestamp: string
  type: string
  data: any
}

export default function TestPage() {
  const [isCreating, setIsCreating] = useState(false)
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null)
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState<string>('pending')
  const [status, setStatus] = useState<'pending' | 'processing' | 'completed' | 'failed'>('pending')
  const [showLogs, setShowLogs] = useState(true)
  const eventSourceRef = useRef<EventSource | null>(null)
  const eventIdRef = useRef(0)

  const addEvent = (type: string, data: any) => {
    const event: SSEEvent = {
      id: eventIdRef.current++,
      timestamp: new Date().toISOString(),
      type,
      data
    }
    setEvents(prev => [...prev, event])
    console.log('SSE Event:', event)
  }

  const startTest = async () => {
    setIsCreating(true)
    setEvents([])
    setProgress(0)
    setProgressMessage(null)
    setCurrentStep('pending')
    setStatus('pending')

    try {
      const response = await apiClient.createVideo(
        "Test Video SSE Integration",
        "This is a test video to verify real-time SSE progress updates work correctly with the backend."
      )

      if (response.success && response.data) {
        const video = response.data
        setCurrentVideoId(video.id)
        setStatus('processing')
        addEvent('video_created', video)

        // Start SSE connection
        if (eventSourceRef.current) {
          eventSourceRef.current.close()
        }

        const eventSource = apiClient.createEventSource(video.id)
        eventSourceRef.current = eventSource

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            addEvent('message', data)

            switch (data.type) {
              case 'progress':
                setProgress(data.progress || 0)
                setProgressMessage(data.message || null)
                break

              case 'status':
              case 'update':
                const updatedVideo = data.data
                setProgress(updatedVideo.progress || 0)
                setCurrentStep(updatedVideo.current_step || 'pending')
                setStatus(updatedVideo.status || 'processing')
                break

              case 'complete':
                const completedVideo = data.data
                setProgress(100)
                setProgressMessage('Video generation complete!')
                setStatus('completed')
                setIsCreating(false)
                eventSource.close()
                break

              case 'error':
                setStatus('failed')
                setProgressMessage(data.message || 'An error occurred')
                setIsCreating(false)
                eventSource.close()
                break

              case 'heartbeat':
                // Keep connection alive
                break
            }
                     } catch (error) {
             addEvent('parse_error', { error: error instanceof Error ? error.message : 'Unknown error', raw: event.data })
           }
        }

        eventSource.onerror = (error) => {
          addEvent('connection_error', error)
          setStatus('failed')
          setProgressMessage('Connection lost')
          setIsCreating(false)
          eventSource.close()
        }

        eventSource.onopen = () => {
          addEvent('connection_opened', { videoId: video.id })
        }
      } else {
        throw new Error(response.error || 'Failed to create video')
      }
         } catch (error) {
       const errorMessage = error instanceof Error ? error.message : 'Unknown error'
       addEvent('create_error', { error: errorMessage })
       setStatus('failed')
       setProgressMessage(errorMessage)
       setIsCreating(false)
     }
  }

  const stopTest = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsCreating(false)
    addEvent('test_stopped', { reason: 'user_action' })
  }

  const clearLogs = () => {
    setEvents([])
    eventIdRef.current = 0
  }

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return (
    <div className="min-h-screen bg-white p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-black mb-2">SSE Integration Test</h1>
          <p className="text-gray-600">Test the real-time Server-Sent Events integration with video creation</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Test Controls */}
          <Card className="border-gray-200">
            <CardHeader>
              <CardTitle>Test Controls</CardTitle>
              <CardDescription>
                Start a test video creation to observe real-time progress updates
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Button
                  onClick={startTest}
                  disabled={isCreating}
                  className="bg-black text-white hover:bg-gray-800"
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Creating Video...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Start Test
                    </>
                  )}
                </Button>
                {isCreating && (
                  <Button
                    onClick={stopTest}
                    variant="outline"
                    className="border-red-300 text-red-700 hover:bg-red-50"
                  >
                    <Pause className="h-4 w-4 mr-2" />
                    Stop Test
                  </Button>
                )}
              </div>

              {currentVideoId && (
                <div className="text-sm text-gray-600">
                  <Label>Video ID:</Label>
                  <code className="ml-2 p-1 bg-gray-100 rounded">{currentVideoId}</code>
                </div>
              )}

              {/* Progress Display */}
              <div className="mt-4">
                <ProgressIndicator
                  progress={progress}
                  message={progressMessage}
                  status={status}
                  currentStep={currentStep}
                  showPercentage={true}
                />
              </div>

              {/* Current Status */}
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <div className="text-sm space-y-1">
                  <div><strong>Status:</strong> {status}</div>
                  <div><strong>Step:</strong> {currentStep}</div>
                  <div><strong>Progress:</strong> {progress}%</div>
                  {progressMessage && (
                    <div><strong>Message:</strong> {progressMessage}</div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Event Logs */}
          <Card className="border-gray-200">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center">
                    <Terminal className="h-5 w-5 mr-2" />
                    Event Logs
                  </CardTitle>
                  <CardDescription>
                    Real-time SSE events ({events.length} events)
                  </CardDescription>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowLogs(!showLogs)}
                  >
                    {showLogs ? 'Hide' : 'Show'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={clearLogs}
                  >
                    Clear
                  </Button>
                </div>
              </div>
            </CardHeader>
            {showLogs && (
              <CardContent>
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {events.length === 0 ? (
                    <div className="text-center text-gray-500 py-4">
                      No events yet. Start a test to see real-time updates.
                    </div>
                  ) : (
                    events.map((event) => (
                      <div key={event.id} className="text-xs border-l-2 border-gray-200 pl-3 py-2">
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-medium text-blue-600">{event.type}</span>
                          <span className="text-gray-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <pre className="text-gray-700 bg-gray-50 p-2 rounded text-xs overflow-x-auto">
{JSON.stringify(event.data, null, 2)}
                        </pre>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            )}
          </Card>
        </div>

        {/* Instructions */}
        <Card className="mt-6 border-gray-200">
          <CardHeader>
            <CardTitle>How to Test</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>1. Click "Start Test" to begin video creation</p>
            <p>2. Watch the progress indicator update in real-time</p>
            <p>3. Monitor the event logs to see SSE messages</p>
            <p>4. Check browser console for additional debug information</p>
            <p>5. The test will automatically complete when video generation finishes</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 