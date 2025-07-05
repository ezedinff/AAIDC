"use client"

import { Loader2, CheckCircle, AlertCircle, Clock } from "lucide-react"
import { cn } from "@/lib/utils"

interface ProgressIndicatorProps {
  progress: number
  message?: string | null
  status: 'pending' | 'processing' | 'completed' | 'failed'
  currentStep?: string
  showPercentage?: boolean
  className?: string
}

export const ProgressIndicator = ({
  progress,
  message,
  status,
  currentStep,
  showPercentage = true,
  className
}: ProgressIndicatorProps) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      case 'processing':
        return 'bg-blue-500'
      default:
        return 'bg-gray-300'
    }
  }

  const getStepDescription = (step: string) => {
    switch (step) {
      case 'scene_generation':
        return 'Generating scenes'
      case 'scene_critique':
        return 'Reviewing quality'
      case 'scene_critique_retry':
        return 'Improving scenes'
      case 'audio_generation':
        return 'Creating audio'
      case 'video_assembly':
        return 'Assembling video'
      default:
        return 'Processing'
    }
  }

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="text-sm font-medium">
            {currentStep ? getStepDescription(currentStep) : 'Progress'}
          </span>
        </div>
        {showPercentage && (
          <span className="text-sm text-gray-500">{progress}%</span>
        )}
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={cn(
            "h-2 rounded-full transition-all duration-300",
            getStatusColor()
          )}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
      
      {message && (
        <p className="text-xs text-gray-600 mt-1">{message}</p>
      )}
    </div>
  )
}

export default ProgressIndicator 