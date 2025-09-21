interface ScoreMeterProps {
  score: number
  size?: "sm" | "md" | "lg"
  className?: string
}

export function ScoreMeter({ score, size = "md", className }: ScoreMeterProps) {
  const sizes = {
    sm: { container: "w-12 h-12", text: "text-xs" },
    md: { container: "w-16 h-16", text: "text-sm" },
    lg: { container: "w-20 h-20", text: "text-base" },
  }

  const config = sizes[size]
  const circumference = 2 * Math.PI * 18 // radius of 18
  const strokeDasharray = circumference
  const strokeDashoffset = circumference - (score / 100) * circumference

  const getColor = (score: number) => {
    if (score >= 80) return "text-green-500"
    if (score >= 60) return "text-yellow-500"
    if (score >= 40) return "text-orange-500"
    return "text-red-500"
  }

  return (
    <div className={`relative ${config.container} ${className}`}>
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 40 40">
        <circle
          cx="20"
          cy="20"
          r="18"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
          className="text-muted-foreground/20"
        />
        <circle
          cx="20"
          cy="20"
          r="18"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          className={`transition-all duration-300 ${getColor(score)}`}
          strokeLinecap="round"
        />
      </svg>
      <div className={`absolute inset-0 flex items-center justify-center ${config.text} font-semibold`}>
        {Math.round(score)}
      </div>
    </div>
  )
}
