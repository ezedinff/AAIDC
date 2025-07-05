const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

export interface Video {
  id: string
  title: string
  description: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  progress_percent: number
  current_step: string
  file_path?: string
  duration?: number
  created_at: string
  updated_at: string
}

export interface VideoProgress {
  id: string
  video_id: string
  step: string
  status: string
  message: string
  timestamp: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP error! status: ${response.status}`,
        }
      }

      return {
        success: true,
        data: data,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request('/api/health')
  }

  // Video operations
  async getVideos(): Promise<ApiResponse<Video[]>> {
    const response = await this.request<{ videos: Video[] }>('/api/videos')
    if (response.success && response.data) {
      return {
        success: true,
        data: response.data.videos || []
      }
    }
    return { success: false, error: response.error || 'Failed to fetch videos' }
  }

  async getVideo(id: string): Promise<ApiResponse<Video>> {
    const response = await this.request<{ video: Video }>(`/api/videos/${id}`)
    if (response.success && response.data) {
      return {
        success: true,
        data: response.data.video
      }
    }
    return { success: false, error: response.error || 'Failed to fetch video' }
  }

  async createVideo(title: string, description: string): Promise<ApiResponse<Video>> {
    const response = await this.request<{ video: Video }>('/api/videos', {
      method: 'POST',
      body: JSON.stringify({ title, description, user_input: description }),
    })
    if (response.success && response.data) {
      return {
        success: true,
        data: response.data.video
      }
    }
    return { success: false, error: response.error || 'Failed to create video' }
  }

  async deleteVideo(id: string): Promise<ApiResponse<{ message: string }>> {
    return this.request(`/api/videos/${id}`, {
      method: 'DELETE',
    })
  }

  async getVideoProgress(id: string): Promise<ApiResponse<VideoProgress[]>> {
    const response = await this.request<{ progress: VideoProgress[] }>(`/api/videos/${id}/progress`)
    if (response.success && response.data) {
      return {
        success: true,
        data: response.data.progress || []
      }
    }
    return { success: false, error: response.error || 'Failed to fetch progress' }
  }

  // Server-Sent Events for real-time updates
  createEventSource(videoId: string): EventSource {
    return new EventSource(`${this.baseUrl}/api/videos/${videoId}/events`)
  }

  // Download video
  getDownloadUrl(videoId: string): string {
    return `${this.baseUrl}/api/videos/${videoId}/download`
  }
}

export const apiClient = new ApiClient()
export default apiClient 