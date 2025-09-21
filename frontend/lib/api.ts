const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/"

export class ApiClient {
  private baseUrl: string
  private mockMode: boolean

  constructor() {
    this.baseUrl = API_BASE
    this.mockMode = typeof window !== "undefined" && new URLSearchParams(window.location.search).has("mock")
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`

    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Products
  async getProducts(sellerId?: string) {
    const params = sellerId ? `?seller_id=${sellerId}` : ""
    return this.request(`products${params}`)
  }

  async getProduct(id: string) {
    return this.request(`products/${id}`)
  }

  async createProduct(data: any) {
    return this.request("products", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async updateProduct(id: string, data: any) {
    return this.request(`products/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  async recheckProduct(id: string) {
    return this.request(`products/${id}/recheck`, {
      method: "POST",
    })
  }

  // Flags
  async getFlags() {
    return this.request("flags")
  }

  // Appeals
  async getAppeals() {
    return this.request("appeals")
  }

  async createAppeal(data: any) {
    return this.request("appeals", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async resolveAppeal(id: string, approve: boolean) {
    return this.request(`appeals/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ approve }),
    })
  }

  // Moderation
  async banProduct(id: string, reason: string) {
    return this.request("moderation/ban", {
      method: "POST",
      body: JSON.stringify({ product_id: id, reason }),
    })
  }

  async reinstateProduct(id: string) {
    return this.request("moderation/reinstate", {
      method: "POST",
      body: JSON.stringify({ product_id: id }),
    })
  }
}

export const apiClient = new ApiClient()
