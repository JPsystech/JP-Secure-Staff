'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { SectionHeader } from '@/components/ui/SectionHeader'
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
    setLoading(true)
    try {
      const body = {
        name: formData.name.trim(),
        mobile: formData.mobile.replace(/\s/g, ''),
        email: formData.email.trim(),
      }
      if (!body.name || !body.mobile || !body.email) {
        toast({
          title: 'Validation',
          description: 'Name, mobile, and email are required.',
          variant: 'destructive',
        })
        setLoading(false)
        return
      }
      const response = await apiRequest<{ id: string }>('/persons', {
        method: 'POST',
        body: JSON.stringify(body),
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
          title: 'Endpoint not available',
          description: 'Create person API did not return data.',
          variant: 'destructive',
        })
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to create person',
        variant: 'destructive',
      })
      if (process.env.NODE_ENV === 'development') {
        console.debug('[CreatePerson] error:', err)
      }
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
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        }
      />

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <SectionHeader
              title="Person details"
              description="Name, mobile (10 digits), and email are required."
            />
          </CardHeader>
          <CardContent className="space-y-4">
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
              <Label htmlFor="mobile">Mobile *</Label>
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
            <div className="flex gap-2 pt-2">
              <Button type="submit" disabled={loading}>
                {loading ? 'Creating...' : 'Create Person'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  )
}
