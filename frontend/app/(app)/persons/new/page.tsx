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
import Link from 'next/link'

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
      const payload = {
        name: formData.name.trim(),
        mobile: formData.mobile.replace(/\s/g, ''),
        email: formData.email.trim(),
      }
      const response = await apiRequest<{ id: string }>('/persons', {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
      })
      if (response.data) {
        toast({ title: 'Success', description: 'Person created successfully' })
        router.push(`/persons`)
      } else if (response.error) {
        toast({ title: 'Error', description: response.error, variant: 'destructive' })
      } else {
        toast({ title: 'Error', description: 'Endpoint not available', variant: 'destructive' })
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Endpoint not available',
        variant: 'destructive',
      })
      if (process.env.NODE_ENV === 'development') {
        console.debug('[CreatePerson] submit error', err)
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
          <Button variant="outline" asChild>
            <Link href="/persons" prefetch={false}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Link>
          </Button>
        }
      />

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <SectionHeader title="Person details" description="Name, mobile and email." />
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
                value={formData.mobile}
                onChange={(e) => setFormData((p) => ({ ...p, mobile: e.target.value }))}
                placeholder="10 digits"
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
              <Button type="button" variant="outline" asChild>
                <Link href="/persons" prefetch={false}>Cancel</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  )
}
