# July 11

https://app.readytensor.ai/publications/WsaE5uxLBqnH
Submission Checklist ✅
To complete this project, you need to submit two deliverables:

Project Publication 📝
Create a short publication on the Ready Tensor platform that:

Describes your project, what it does, and how it works
Follows best practices from our Technical Evaluation Rubric for the
Tool / App / Software Development category
Meets at least 70% of the listed criteria



Project GitHub Repository 🗂️
Submit a repo that:

Contains clean, working code for your multi-agent system
Defines roles and communication flows between agents
Includes setup instructions and sample interactions
Meets the “Essential” level of our repo evaluation rubric
Satisfies at least 70% of the Essential criteria




# My Project idea
agentic ai video generator

user types in about the video idea and give context ```->```
ai takes the idea and generate video scene based on prompt configuration
```->```
crtiic the scene to improve it with ai and human
```->```
generate audio for each scene
```->```
generate the video


```mermaid
graph LR
    %% Main Workflow
    START([User Input<br/>Video Idea]) --> SCENE[Scene Generator<br/>Agent]
    SCENE --> CRITIC[Scene Critic<br/>Agent]
    CRITIC --> AUDIO[Audio<br/>Agent]
    AUDIO --> VIDEO[Video Assembly<br/>Agent]
    VIDEO --> END([Final Video<br/>MP4])
    
    %% State Flow
    subgraph "LangGraph State"
        STATE1[user_input: str]
        STATE2[raw_scenes: List]
        STATE3[improved_scenes: List]
        STATE4[audio_files: List]
        STATE5[final_video: str]
    end
    
    %% External Services
    subgraph "External APIs"
        GPT[OpenAI GPT-4]
        TTS[OpenAI TTS]
        SD[Stable Diffusion]
        FFMPEG[FFmpeg]
    end
    
    %% Agent to Service Connections
    SCENE --> GPT
    CRITIC --> GPT
    AUDIO --> TTS
    VIDEO --> SD
    VIDEO --> FFMPEG
    
    %% State Updates
    START -.-> STATE1
    SCENE -.-> STATE2
    CRITIC -.-> STATE3
    AUDIO -.-> STATE4
    VIDEO -.-> STATE5
    
    %% Styling
    classDef agent fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef state fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    classDef endpoint fill:#fff3e0,stroke:#ff9800,stroke-width:3px
    
    class SCENE,CRITIC,AUDIO,VIDEO agent
    class GPT,TTS,SD,FFMPEG service
    class STATE1,STATE2,STATE3,STATE4,STATE5 state
    class START,END endpoint
```



Title: "The Ancient Origins of Coffee: Ethiopia's Gift to the World"
Description: "Discover how coffee was first discovered in the highlands of Ethiopia over 1,000 years ago. From the legendary goat herder Kaldi who noticed his goats becoming energetic after eating coffee berries, to how Ethiopian monks used coffee to stay alert during prayers. Learn about the ancient coffee ceremonies that still exist today and how this magical bean spread from Ethiopia to Yemen, then to the rest of the world."