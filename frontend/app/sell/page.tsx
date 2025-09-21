"use client"

import type React from "react"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"
import { Loader2, CheckCircle } from "lucide-react"

export default function SellPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const isMockMode = searchParams.get("mock") === "1"

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    category: "",
    price: "",
    inventory: "",
    image_url: "",
  })

  const categories = [
    "Electronics",
    "Baby Food",
    "Health",
    "Sports",
    "Supplements",
    "Home",
    "Beauty",
    "Toys",
    "Books",
    "Clothing",
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const productData = {
        seller_id: "me",
        title: formData.title,
        description: formData.description,
        category: formData.category || undefined,
        price: formData.price ? Number.parseFloat(formData.price) : undefined,
        inventory: formData.inventory ? Number.parseInt(formData.inventory) : undefined,
        image_url: formData.image_url || undefined,
      }

      if (isMockMode) {
        // Mock submission
        await new Promise((resolve) => setTimeout(resolve, 1000))
        setSubmitted(true)

        // Mock compliance check
        setTimeout(() => {
          toast({
            title: "Compliance scan queued",
            description: "Your listing will be reviewed for regulatory compliance.",
          })
        }, 500)
      } else {
        const product = await apiClient.createProduct(productData)

        // Trigger compliance check
        apiClient.recheckProduct(product.id).catch(console.error)

        setSubmitted(true)
        toast({
          title: "Listing created successfully",
          description: "Compliance scan has been queued.",
        })
      }
    } catch (error) {
      toast({
        title: "Error creating listing",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container py-8">
          <div className="max-w-md mx-auto text-center space-y-6">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold mb-2">Listing Submitted!</h1>
              <p className="text-muted-foreground mb-4">
                Your product has been submitted and is pending compliance scan.
              </p>
              <div className="space-y-2">
                <Button onClick={() => router.push("/seller/listings")} className="w-full">
                  View My Listings
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setSubmitted(false)
                    setFormData({
                      title: "",
                      description: "",
                      category: "",
                      price: "",
                      inventory: "",
                      image_url: "",
                    })
                  }}
                  className="w-full"
                >
                  Add Another Listing
                </Button>
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container py-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Add New Listing</h1>
            <p className="text-muted-foreground">
              Create a new product listing. All listings are automatically scanned for regulatory compliance.
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Product Details</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="title">Product Title *</Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => handleInputChange("title", e.target.value)}
                    placeholder="Enter product title"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange("description", e.target.value)}
                    placeholder="Describe your product in detail"
                    rows={4}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="category">Category</Label>
                    <Select value={formData.category} onValueChange={(value) => handleInputChange("category", value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map((category) => (
                          <SelectItem key={category} value={category}>
                            {category}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="price">Price ($)</Label>
                    <Input
                      id="price"
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.price}
                      onChange={(e) => handleInputChange("price", e.target.value)}
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="inventory">Inventory</Label>
                    <Input
                      id="inventory"
                      type="number"
                      min="0"
                      value={formData.inventory}
                      onChange={(e) => handleInputChange("inventory", e.target.value)}
                      placeholder="Available quantity"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="image_url">Image URL</Label>
                    <Input
                      id="image_url"
                      type="url"
                      value={formData.image_url}
                      onChange={(e) => handleInputChange("image_url", e.target.value)}
                      placeholder="https://example.com/image.jpg"
                    />
                  </div>
                </div>

                <div className="flex gap-4 pt-4">
                  <Button type="submit" disabled={loading} className="flex-1">
                    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Create Listing
                  </Button>
                  <Button type="button" variant="outline" onClick={() => router.back()}>
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
