"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { ChevronLeft, ChevronRight, Download, Play, Pause, Video, Loader2, AlertCircle, CheckCircle, Trash2 } from "lucide-react"
import { useVideoCreation } from "@/lib/hooks/useVideoCreation"
import { useVideoLibrary } from "@/lib/hooks/useVideoLibrary"
import { ApiStatus } from "@/components/api-status"
import { ProgressIndicator } from "@/components/progress-indicator"

export default function Component() {
  const [showForm, setShowForm] = useState(false)
  const [videoTitle, setVideoTitle] = useState("")
  const [videoDescription, setVideoDescription] = useState("")
  const [isPlaying, setIsPlaying] = useState(false)

  // Use custom hooks for backend integration
  const videoCreation = useVideoCreation()
  const videoLibrary = useVideoLibrary()

  // Auto-subscribe to updates when video is created
  useEffect(() => {
    if (videoCreation.video && videoCreation.video.id) {
      console.log('Starting SSE connection for video:', videoCreation.video.id)
      const cleanup = videoCreation.subscribeToUpdates(videoCreation.video.id)
      return cleanup
    }
  }, [videoCreation.video?.id, videoCreation.subscribeToUpdates])

  // Auto-progress steps based on backend status
  useEffect(() => {
    if (videoCreation.video) {
      const currentBackendStep = videoCreation.video.current_step
      const targetStep = videoCreation.stepMapping[currentBackendStep]
      
      if (targetStep && targetStep !== videoCreation.currentStep) {
        videoCreation.setCurrentStep(targetStep)
      }
    }
  }, [videoCreation.video?.current_step, videoCreation.stepMapping, videoCreation.currentStep, videoCreation.setCurrentStep])

  const handleCreateVideo = async () => {
    if (!videoTitle.trim() || !videoDescription.trim()) {
      return
    }

    try {
      console.log('Creating video:', { title: videoTitle, description: videoDescription })
      const video = await videoCreation.createVideo(videoTitle, videoDescription)
      console.log('Video created successfully:', video)
      // Video creation started, keep the form open to show progress
    } catch (error) {
      console.error('Error creating video:', error)
    }
  }

  const handleCreateView = () => {
    setShowForm(true)
    setVideoTitle("")
    setVideoDescription("")
    videoCreation.reset()
  }

  const handleCancelCreate = () => {
    setShowForm(false)
    videoCreation.reset()
  }

  const handleComplete = () => {
    setShowForm(false)
    videoCreation.reset()
    // Refresh video library to show new video
    videoLibrary.loadVideos()
  }

  const handleDeleteVideo = async (videoId: string) => {
    if (confirm('Are you sure you want to delete this video?')) {
      await videoLibrary.deleteVideo(videoId)
    }
  }

  const getStepTitle = (step: number) => {
    switch (step) {
      case 1:
        return "Video Description"
      case 2:
        return "Scene Preview"
      case 3:
        return "Audio Preview"
      case 4:
        return "Final Video"
      default:
        return "Unknown Step"
    }
  }

  const getStepDescription = (step: number) => {
    switch (step) {
      case 1:
        return "Describe the video you want to create"
      case 2:
        return "Show a preview of the generated scenes and allow review"
      case 3:
        return "Play the generated audio clips for each scene"
      case 4:
        return "Display the final video with download option"
      default:
        return ""
    }
  }

  const renderStepContent = () => {
    const step = videoCreation.currentStep

    switch (step) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="title" className="text-sm font-medium">
                Video Title
              </Label>
              <Textarea
                id="title"
                placeholder="Enter a catchy title for your video..."
                value={videoTitle}
                onChange={(e) => setVideoTitle(e.target.value)}
                className="mt-2 min-h-[60px] border-gray-300 focus:border-black"
              />
            </div>
            <div>
              <Label htmlFor="description" className="text-sm font-medium">
                Video Description
              </Label>
              <Textarea
                id="description"
                placeholder="Describe the video you want to create in detail..."
                value={videoDescription}
                onChange={(e) => setVideoDescription(e.target.value)}
                className="mt-2 min-h-[120px] border-gray-300 focus:border-black"
              />
            </div>
          </div>
        )
      case 2:
        return (
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium">Scene Generation & Review</Label>
              <div className="mt-2 aspect-video bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <div className="flex items-center justify-center mb-2">
                    {videoCreation.isProcessing && (
                      videoCreation.video?.current_step === 'scene_generation' || 
                      videoCreation.video?.current_step === 'scene_critique' || 
                      videoCreation.video?.current_step === 'scene_critique_retry'
                    ) ? (
                      <Loader2 className="h-8 w-8 animate-spin mr-2" />
                    ) : (
                      <CheckCircle className="h-8 w-8 text-green-500 mr-2" />
                    )}
                    <Video className="h-8 w-8" />
                  </div>
                  <p className="text-sm font-medium">
                    {videoCreation.progressMessage || 
                      (videoCreation.video?.current_step === 'scene_generation' ? 
                        'AI is generating video scenes...' :
                        videoCreation.video?.current_step === 'scene_critique' ||
                        videoCreation.video?.current_step === 'scene_critique_retry' ?
                        'AI is reviewing and improving scenes...' :
                        'Scene generation complete'
                      )
                    }
                  </p>
                  <p className="text-xs mt-1">Based on: "{videoDescription}"</p>
                  {videoCreation.video?.current_step === 'scene_critique_retry' && (
                    <p className="text-xs mt-1 text-orange-600">
                      Quality review in progress - ensuring optimal scenes
                    </p>
                  )}
                </div>
              </div>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-700">
                {videoCreation.progressMessage || 
                  `The AI is analyzing your description and generating optimized video scenes. 
                  ${videoCreation.video?.current_step === 'scene_critique' || 
                    videoCreation.video?.current_step === 'scene_critique_retry' ? 
                    'The AI is now reviewing and improving the scenes for better quality.' : 
                    'This process may take a few minutes.'
                  }`
                }
              </p>
            </div>
          </div>
        )
      case 3:
        return (
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium">Audio Generation</Label>
              <div className="mt-2 space-y-3">
                {[1, 2, 3].map((trackNumber) => (
                  <div key={trackNumber} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center">
                      {videoCreation.isProcessing && videoCreation.video?.current_step === 'audio_generation' ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                      )}
                      <Button variant="outline" size="sm" disabled className="border-gray-300">
                        <Play className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium">Scene {trackNumber} Audio</div>
                      <div className="text-xs text-gray-500">
                        {videoCreation.video?.current_step === 'audio_generation' ? 
                          'Generating audio...' : 
                          'Audio ready'
                        }
                      </div>
                    </div>
                    <div className="w-32 h-1 bg-gray-200 rounded-full">
                      <div className={`h-1 bg-blue-600 rounded-full ${
                        videoCreation.video?.current_step === 'audio_generation' ? 'w-2/3 animate-pulse' : 'w-full'
                      }`}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-700">
                {videoCreation.progressMessage || 
                  'AI is generating high-quality audio narration for your video scenes with natural-sounding voices.'
                }
              </p>
            </div>
          </div>
        )
      case 4:
        if (videoCreation.video?.status === 'completed') {
          return (
            <div className="space-y-4">
              <div>
                <Label className="text-sm font-medium">Final Video</Label>
                <div className="mt-2 aspect-video bg-black rounded-lg flex items-center justify-center relative overflow-hidden">
                  <div className="text-center text-white">
                    <CheckCircle className="mx-auto h-16 w-16 mb-3 text-green-400" />
                    <p className="text-lg font-medium">Video Ready!</p>
                    <p className="text-sm opacity-75">
                      Duration: {videoLibrary.formatDuration(videoCreation.video.duration)}
                    </p>
                  </div>
                </div>
              </div>
              <Button 
                className="w-full bg-black text-white hover:bg-gray-800"
                onClick={() => {
                  const downloadUrl = videoLibrary.getDownloadUrl(videoCreation.video!.id)
                  window.open(downloadUrl, '_blank')
                }}
              >
                <Download className="h-4 w-4 mr-2" />
                Download Video
              </Button>
            </div>
          )
        } else if (videoCreation.video?.status === 'failed') {
          return (
            <div className="space-y-4">
              <div>
                <Label className="text-sm font-medium">Video Generation Failed</Label>
                <div className="mt-2 aspect-video bg-red-100 border-2 border-red-300 rounded-lg flex items-center justify-center">
                  <div className="text-center text-red-700">
                    <AlertCircle className="mx-auto h-16 w-16 mb-3" />
                    <p className="text-lg font-medium">Generation Failed</p>
                    <p className="text-sm opacity-75">
                      {videoCreation.error || 'An error occurred during video generation'}
                    </p>
                  </div>
                </div>
              </div>
              <Button 
                variant="outline"
                className="w-full border-red-300 text-red-700 hover:bg-red-50"
                onClick={() => {
                  handleCancelCreate()
                }}
              >
                Try Again
              </Button>
            </div>
          )
        } else {
          return (
            <div className="space-y-4">
              <div>
                <Label className="text-sm font-medium">Video Assembly</Label>
                <div className="mt-2 aspect-video bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <div className="flex items-center justify-center mb-2">
                      <Loader2 className="h-8 w-8 animate-spin mr-2" />
                      <Video className="h-8 w-8" />
                    </div>
                    <p className="text-sm font-medium">
                      {videoCreation.progressMessage || 'Assembling final video...'}
                    </p>
                    <p className="text-xs mt-1">Almost done!</p>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-700">
                  {videoCreation.progressMessage || 
                    'AI is combining all elements to create your final video. This is the last step!'
                  }
                </p>
              </div>
            </div>
          )
        }
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-black">AI Video Generator</h1>
              <div className="mt-2">
                <ApiStatus />
              </div>
            </div>
            {!showForm && (
              <Button onClick={handleCreateView} className="bg-black text-white hover:bg-gray-800">
                Create Video
              </Button>
            )}
          </div>
        </div>

        {/* Form Section */}
        {showForm && (
          <Card className="mb-8 border-gray-200">
            <CardHeader className="border-b border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl">Create New Video</CardTitle>
                  <CardDescription>
                    {getStepTitle(videoCreation.currentStep)} - {getStepDescription(videoCreation.currentStep)}
                  </CardDescription>
                </div>
                <Button 
                  variant="outline" 
                  onClick={handleCancelCreate} 
                  className="border-gray-300"
                  disabled={videoCreation.isLoading}
                >
                  Cancel
                </Button>
              </div>

              {/* Step Indicator */}
              <div className="flex items-center space-x-2 mt-4">
                {[1, 2, 3, 4].map((step) => (
                  <div key={step} className="flex items-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        step <= videoCreation.currentStep ? "bg-black text-white" : "bg-gray-200 text-gray-500"
                      }`}
                    >
                      {step}
                    </div>
                    {step < 4 && <div className={`w-12 h-0.5 ${step < videoCreation.currentStep ? "bg-black" : "bg-gray-200"}`} />}
                  </div>
                ))}
              </div>

              {/* Progress Bar */}
              {videoCreation.video && (
                <div className="mt-4">
                  <ProgressIndicator
                    progress={videoCreation.progressPercent}
                    message={videoCreation.progressMessage}
                    status={videoCreation.video.status}
                    currentStep={videoCreation.video.current_step}
                    showPercentage={true}
                  />
                </div>
              )}
            </CardHeader>

            <CardContent className="pt-6">
              {renderStepContent()}

              {/* Error Display */}
              {videoCreation.error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700">{videoCreation.error}</p>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex justify-between mt-6">
                <Button
                  variant="outline"
                  onClick={handleCancelCreate}
                  disabled={videoCreation.isLoading}
                  className="border-gray-300 bg-transparent"
                >
                  <ChevronLeft className="h-4 w-4 mr-2" />
                  Cancel
                </Button>

                {videoCreation.currentStep === 1 ? (
                  <Button
                    onClick={handleCreateVideo}
                    disabled={!videoTitle.trim() || !videoDescription.trim() || videoCreation.isLoading}
                    className="bg-black text-white hover:bg-gray-800"
                  >
                    {videoCreation.isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        Create Video
                        <ChevronRight className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                ) : videoCreation.currentStep === 2 ? (
                  <Button 
                    onClick={() => videoCreation.setCurrentStep(3)}
                    className="bg-black text-white hover:bg-gray-800"
                    disabled={videoCreation.isProcessing && (
                      videoCreation.video?.current_step === 'scene_generation' || 
                      videoCreation.video?.current_step === 'scene_critique' || 
                      videoCreation.video?.current_step === 'scene_critique_retry'
                    )}
                  >
                    {videoCreation.isProcessing && (
                      videoCreation.video?.current_step === 'scene_generation' || 
                      videoCreation.video?.current_step === 'scene_critique' || 
                      videoCreation.video?.current_step === 'scene_critique_retry'
                    ) ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        Continue to Audio
                        <ChevronRight className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                ) : videoCreation.currentStep === 3 ? (
                  <Button 
                    onClick={() => videoCreation.setCurrentStep(4)}
                    className="bg-black text-white hover:bg-gray-800"
                    disabled={videoCreation.isProcessing && videoCreation.video?.current_step === 'audio_generation'}
                  >
                    {videoCreation.isProcessing && videoCreation.video?.current_step === 'audio_generation' ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        Continue to Final Video
                        <ChevronRight className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                ) : (
                  <Button 
                    onClick={handleComplete} 
                    className="bg-black text-white hover:bg-gray-800"
                    disabled={videoCreation.isProcessing}
                  >
                    {videoCreation.video?.status === 'completed' ? 'Complete' : 'Processing...'}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Video Library Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-black">Video Library</h2>
            <Button 
              variant="outline" 
              onClick={videoLibrary.loadVideos}
              disabled={videoLibrary.isLoading}
              className="border-gray-300"
            >
              {videoLibrary.isLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                'Refresh'
              )}
            </Button>
          </div>

          {videoLibrary.error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{videoLibrary.error}</p>
            </div>
          )}

          {videoLibrary.isLoading && videoLibrary.videos.length === 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="border-gray-200 animate-pulse">
                  <CardContent className="p-0">
                    <div className="h-32 bg-gray-200 rounded-t-lg" />
                    <div className="p-4">
                      <div className="h-4 bg-gray-200 rounded mb-2" />
                      <div className="h-8 bg-gray-200 rounded" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
                     ) : !Array.isArray(videoLibrary.videos) || videoLibrary.videos.length === 0 ? (
            <div className="text-center py-12">
              <Video className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <p className="text-gray-600">No videos created yet.</p>
              <p className="text-sm text-gray-500 mt-1">Click "Create Video" to get started!</p>
            </div>
          ) : (
                         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
               {Array.isArray(videoLibrary.videos) && videoLibrary.videos.map((video) => (
                <Card key={video.id} className="border-gray-200 hover:shadow-md transition-shadow">
                  <CardContent className="p-0">
                    <div className="relative">
                      <div className="w-full h-32 bg-gray-100 rounded-t-lg flex items-center justify-center">
                        <Video className="h-12 w-12 text-gray-400" />
                      </div>
                      <div className="absolute top-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                        {videoLibrary.formatDuration(video.duration)}
                      </div>
                      <div className={`absolute top-2 left-2 text-xs px-2 py-1 rounded ${
                        video.status === 'completed' ? 'bg-green-100 text-green-800' :
                        video.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                        video.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {videoLibrary.getStatusText(video.status)}
                      </div>
                    </div>
                    <div className="p-4">
                      <h3 className="font-medium text-black mb-1">{video.title}</h3>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{video.description}</p>
                      <div className="flex space-x-2">
                        {video.status === 'completed' && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1 border-gray-300 hover:bg-gray-50 bg-transparent"
                            onClick={() => {
                              const downloadUrl = videoLibrary.getDownloadUrl(video.id)
                              window.open(downloadUrl, '_blank')
                            }}
                          >
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-red-300 text-red-700 hover:bg-red-50"
                          onClick={() => handleDeleteVideo(video.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

