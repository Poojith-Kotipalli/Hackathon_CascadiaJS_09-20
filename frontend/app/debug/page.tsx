"use client"

import { useState, useEffect } from "react"
import { Navigation } from "@/components/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { useSearchParams, useRouter } from "next/navigation"
import { Bug, Server, Database, Zap } from "lucide-react"

export default function DebugPage() {
  const [apiHealth, setApiHealth] = useState<any>(null)
  const [lastRequest, setLastRequest] = useState<any>(null)
  const [lastResponse, setLastResponse] = useState<any>(null)
  const [mockMode, setMockMode] = useState(false)

  const searchParams = useSearchParams()
  const router = useRouter()

  useEffect(() => {
    setMockMode(searchParams.get("mock") === "1")
    checkApiHealth()
  }, [searchParams])

  const checkApiHealth = async () => {
    try {
      const response = await fetch("/api/health")
      const data = await response.json()
      setApiHealth(data)
    } catch (error) {
      setApiHealth({ error: error instanceof Error ? error.message : "API unavailable" })
    }
  }

  const toggleMockMode = () => {
    const newSearchParams = new URLSearchParams(searchParams)
    if (mockMode) {
      newSearchParams.delete("mock")
    } else {
      newSearchParams.set("mock", "1")
    }
    router.push(`/debug?${newSearchParams.toString()}`)
  }

  const testApiEndpoint = async (endpoint: string, method = "GET") => {
    try {
      const startTime = Date.now()
      const response = await fetch(`/api/${endpoint}`, { method })
      const endTime = Date.now()
      const data = await response.json()

      setLastRequest({
        endpoint: `/api/${endpoint}`,
        method,
        timestamp: new Date().toISOString(),
        duration: endTime - startTime,
      })

      setLastResponse({
        status: response.status,
        statusText: response.statusText,
        data,
        timestamp: new Date().toISOString(),
      })
    } catch (error) {
      setLastResponse({
        error: error instanceof Error ? error.message : "Request failed",
        timestamp: new Date().toISOString(),
      })
    }
  }

  const endpoints = [
    { name: "Health Check", endpoint: "health", method: "GET" },
    { name: "Get Products", endpoint: "products", method: "GET" },
    { name: "Get Flags", endpoint: "flags", method: "GET" },
    { name: "Get Appeals", endpoint: "appeals", method: "GET" },
  ]

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container py-8">
        <div className="flex items-center gap-3 mb-6">
          <Bug className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">Debug Console</h1>
            <p className="text-muted-foreground">Monitor API requests, responses, and system status</p>
          </div>
        </div>

        <div className="grid gap-6">
          {/* System Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">Mode</p>
                    <p className="text-sm text-muted-foreground">{mockMode ? "Mock (Offline)" : "Live API"}</p>
                  </div>
                  <Badge variant={mockMode ? "secondary" : "default"}>{mockMode ? "Mock" : "Live"}</Badge>
                </div>

                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">API Status</p>
                    <p className="text-sm text-muted-foreground">{apiHealth?.status || "Checking..."}</p>
                  </div>
                  <Badge variant={apiHealth?.status === "OK" ? "default" : "destructive"}>
                    {apiHealth?.status === "OK" ? "Online" : "Offline"}
                  </Badge>
                </div>

                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">Database</p>
                    <p className="text-sm text-muted-foreground">{mockMode ? "In-Memory" : "SQLite"}</p>
                  </div>
                  <Database className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>

              <div className="flex items-center space-x-2 mt-4 pt-4 border-t">
                <Switch id="mock-mode" checked={mockMode} onCheckedChange={toggleMockMode} />
                <Label htmlFor="mock-mode">Enable Mock Mode (offline development)</Label>
              </div>
            </CardContent>
          </Card>

          {/* API Testing */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                API Testing
              </CardTitle>
              <CardDescription>Test API endpoints and view request/response data</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-6">
                {endpoints.map((endpoint) => (
                  <Button
                    key={endpoint.endpoint}
                    variant="outline"
                    size="sm"
                    onClick={() => testApiEndpoint(endpoint.endpoint, endpoint.method)}
                  >
                    {endpoint.name}
                  </Button>
                ))}
              </div>

              <Tabs defaultValue="request" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="request">Last Request</TabsTrigger>
                  <TabsTrigger value="response">Last Response</TabsTrigger>
                </TabsList>

                <TabsContent value="request" className="mt-4">
                  <div className="border rounded-lg p-4 bg-muted/50">
                    {lastRequest ? (
                      <pre className="text-sm overflow-auto">{JSON.stringify(lastRequest, null, 2)}</pre>
                    ) : (
                      <p className="text-muted-foreground">No requests made yet</p>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="response" className="mt-4">
                  <div className="border rounded-lg p-4 bg-muted/50">
                    {lastResponse ? (
                      <pre className="text-sm overflow-auto">{JSON.stringify(lastResponse, null, 2)}</pre>
                    ) : (
                      <p className="text-muted-foreground">No responses received yet</p>
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Environment Info */}
          <Card>
            <CardHeader>
              <CardTitle>Environment Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">API Base URL:</span>
                  <span className="font-mono">{process.env.NEXT_PUBLIC_API_BASE || "/api/"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Environment:</span>
                  <span className="font-mono">{process.env.NODE_ENV || "development"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Build Time:</span>
                  <span className="font-mono">{new Date().toISOString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
