'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { apiRequest } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { ArrowLeft } from 'lucide-react'

export default function CreatePersonPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    mobile: '',
    email: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const name = formData.name.trim()
    const mobile = (formData.mobile || '').replace(/\s/g, '')
    const email = formData.email.trim()
    if (!name || !mobile || !email) {
      toast({
        title: 'Validation',
        description: 'Name, phone and email are required.',
        variant: 'destructive',
      })
      return
    }
    if (!/^[0-9]{10}$/.test(mobile)) {
      toast({
        title: 'Validation',
        description: 'Mobile must be exactly 10 digits.',
        variant: 'destructive',
      })
      return
    }
    setLoading(true)
    try {
      const response = await apiRequest<{ id: string }>('/persons', {
        method: 'POST',
        body: JSON.stringify({ name, mobile, email }),
      })
      if (response.data?.id) {
        toast({ title: 'Success', description: 'Person created successfully.' })
        router.push(`/persons/${response.data.id}`)
      } else if (response.error) {
        toast({
          title: 'Error',
          description: response.error,
          variant: 'destructive',
        })
      } else {
        toast({
          title: 'Error',
          description: 'Endpoint not available or unexpected response.',
          variant: 'destructive',
        })
      }
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.debug('[CreatePerson] submit error', err)
      }
      toast({
        title: 'Error',
        description: 'Endpoint not available or request failed.',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create Person"
        subtitle="Add a new person (name, phone, email)"
        actions={
          <Button variant="outline" asChild>
            <Link href="/persons" prefetch={false}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Link>
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Person details</h3>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
            <div>
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData((p) => ({ ...p, name: e.target.value }))}
                placeholder="Full name"
                required
              />
            </div>
            <div>
              <Label htmlFor="mobile">Phone (10 digits) *</Label>
              <Input
                id="mobile"
                type="tel"
                value={formData.mobile}
                onChange={(e) => setFormData((p) => ({ ...p, mobile: e.target.value }))}
                placeholder="10 digits"
                maxLength={10}
                required
              />
            </div>
            <div>
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData((p) => ({ ...p, email: e.target.value }))}
                placeholder="email@example.com"
                required
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={loading}>
                {loading ? 'Creating...' : 'Create Person'}
              </Button>
              <Button type="button" variant="outline" asChild>
                <Link href="/persons" prefetch={false}>Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
