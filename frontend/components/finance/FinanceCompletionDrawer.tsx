'use client'

import { useState, useEffect } from 'react'
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerFooter,
} from '@/components/ui/drawer'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { apiRequest, apiFetch } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { Loader2, CheckCircle2, Upload, X, FileText, Download } from 'lucide-react'

interface Person {
  id: string
  name: string
  mobile: string
  email?: string
  stream?: string
  location?: string
}

interface Company {
  id: number
  name: string
  short_code: string
  is_akshar: boolean
}

interface FinanceCompletionDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  person: Person | null
  onComplete: () => void
}

export function FinanceCompletionDrawer({
  open,
  onOpenChange,
  person,
  onComplete,
}: FinanceCompletionDrawerProps) {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [companies, setCompanies] = useState<Company[]>([])
  const [uploadingDoc, setUploadingDoc] = useState(false)
  const [kycDocuments, setKycDocuments] = useState<Array<{id: number, doc_name: string, file_key: string, created_at: string, doc_category?: string}>>([])
  const [formData, setFormData] = useState({
    employment_type: '' as 'PERMANENT' | 'FREELANCER' | 'CONTRACTUAL' | '',
    company_id: '',
    aadhaar: '',
    pan: '',
    bank_account_no: '',
    ifsc: '',
    bank_name: '',
    branch: '',
    plan_type: '' as 'MANDAY' | 'MANMONTH' | 'MONTHLY_SALARY' | '',
    amount: '',
    valid_from: '',
    valid_to: '',
    working_day_mode: '',
    project_id: '',
  })
  const [employeeCodePreview, setEmployeeCodePreview] = useState<string>('')

  useEffect(() => {
    if (open && person) {
      fetchCompanies()
      resetForm()
      fetchExistingKycAndSetForm()
      fetchKycDocuments()
    }
  }, [open, person])

  const fetchExistingKycAndSetForm = async () => {
    if (!person) return
    try {
      const response = await apiRequest<{
        aadhaar?: string | null
        pan?: string | null
        bank_account_no?: string | null
        ifsc?: string | null
        bank_name?: string | null
        branch?: string | null
      }>(`/finance/persons/${person.id}/kyc`)
      if (response.data) {
        setFormData((prev) => ({
          ...prev,
          aadhaar: response.data?.aadhaar ?? '',
          pan: response.data?.pan ?? '',
          bank_account_no: response.data?.bank_account_no ?? '',
          ifsc: response.data?.ifsc ?? '',
          bank_name: response.data?.bank_name ?? '',
          branch: response.data?.branch ?? '',
        }))
      }
    } catch {
      // No KYC yet: form already reset in useEffect
    }
  }
  
  const fetchKycDocuments = async () => {
    if (!person) return
    try {
      const response = await apiRequest<{items: Array<{id: number, doc_name: string, file_key: string, created_at: string}>}>(`/cv-wallet/persons/${person.id}/finance-hr-docs`)
      if (response.data) {
        // Since 'categories' does not exist on the returned data, just filter from response.data.items
        const financeDocs = (response.data.items || []).filter(
          (doc: any) => doc.doc_category === 'FINANCE_KYC'
        )
        setKycDocuments(financeDocs)
      }
    } catch (err) {
      console.error('Failed to fetch KYC documents')
      setKycDocuments([])
    }
  }

  useEffect(() => {
    if (formData.employment_type && formData.company_id) {
      // Preview employee code (actual generation happens on backend)
      const company = companies.find(c => c.id.toString() === formData.company_id)
      if (company) {
        if (company.is_akshar) {
          if (formData.employment_type === 'PERMANENT') {
            setEmployeeCodePreview('ACP-XXX')
          } else if (formData.employment_type === 'FREELANCER') {
            setEmployeeCodePreview('ACF-XXX')
          } else if (formData.employment_type === 'CONTRACTUAL') {
            setEmployeeCodePreview('ACM-XXX')
          }
        } else {
          setEmployeeCodePreview(`${company.short_code}-XXX`)
        }
      }
    } else {
      setEmployeeCodePreview('')
    }
  }, [formData.employment_type, formData.company_id, companies])

  const fetchCompanies = async () => {
    try {
      const response = await apiRequest<Company[]>('/master-data/companies')
      if (response.data) {
        setCompanies(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch companies')
    }
  }

  const resetForm = () => {
    setFormData({
      employment_type: '',
      company_id: '',
      aadhaar: '',
      pan: '',
      bank_account_no: '',
      ifsc: '',
      bank_name: '',
      branch: '',
      plan_type: '',
      amount: '',
      valid_from: '',
      valid_to: '',
      working_day_mode: '',
      project_id: '',
    })
    setEmployeeCodePreview('')
  }

  const handleSave = async () => {
    if (!person) return

    setLoading(true)
    try {
      // Step 1: Assign employment
      if (formData.employment_type && formData.company_id) {
        await apiRequest(`/finance/persons/${person.id}/assign`, {
          method: 'POST',
          body: JSON.stringify({
            employment_type: formData.employment_type,
            company_id: parseInt(formData.company_id),
          }),
        })
      }

      // Step 2: Add KYC (bank_name required)
      if (formData.bank_name?.trim()) {
        await apiRequest(`/finance/persons/${person.id}/kyc`, {
          method: 'POST',
          body: JSON.stringify({
            aadhaar: formData.aadhaar || null,
            pan: formData.pan || null,
            bank_account_no: formData.bank_account_no || null,
            ifsc: formData.ifsc || null,
            bank_name: formData.bank_name.trim(),
            branch: formData.branch || null,
          }),
        })
      }

      // Step 3: Add rate plan
      // For PERMANENT, use MONTHLY_SALARY as plan_type
      const planTypeToUse = formData.employment_type === 'PERMANENT' ? 'MONTHLY_SALARY' : formData.plan_type
      if (planTypeToUse && formData.amount && formData.valid_from) {
        // FIXED: Clean up empty strings and convert types properly
        const ratePlanData: any = {
          plan_type: planTypeToUse,
          amount: parseFloat(formData.amount),
          valid_from: formData.valid_from,
          valid_to: formData.valid_to || null,
          working_day_mode: formData.working_day_mode || null,
          project_id: formData.project_id ? parseInt(formData.project_id) : null,
        }
        
        // Remove empty strings
        Object.keys(ratePlanData).forEach(key => {
          if (ratePlanData[key] === '' || ratePlanData[key] === 0) {
            ratePlanData[key] = null
          }
        })
        
        await apiRequest(`/finance/persons/${person.id}/rate-plan`, {
          method: 'POST',
          body: JSON.stringify(ratePlanData),
        })
      }

      toast({
        title: 'Saved',
        description: 'Finance details saved successfully',
      })
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err?.error || 'Failed to save finance details',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const hasRequiredKycDocs = (): boolean => {
    const names = kycDocuments.map((d) => (d.doc_name || '').toLowerCase())
    const hasAadhaar = names.some((n) => n.includes('aadhaar') || n.includes('aadhar'))
    const hasPan = names.some((n) => n.includes('pan'))
    const hasCheque = names.some((n) => n.includes('cancelled') && (n.includes('cheque') || n.includes('passbook')))
    return hasAadhaar && hasPan && hasCheque
  }

  const handleSubmitToHR = async () => {
    if (!person) return

    // Validate required fields
    if (!formData.employment_type || !formData.company_id) {
      toast({
        title: 'Validation Error',
        description: 'Please select employment type and company',
        variant: 'destructive',
      })
      return
    }

    if (!formData.aadhaar || !formData.pan) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in Aadhaar and PAN',
        variant: 'destructive',
      })
      return
    }

    if (!formData.bank_name?.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Bank name is required',
        variant: 'destructive',
      })
      return
    }

    if (!hasRequiredKycDocs()) {
      toast({
        title: 'Validation Error',
        description: 'Please upload all required documents: Aadhaar card, PAN card, and Cancelled cheque',
        variant: 'destructive',
      })
      return
    }

    if (!formData.bank_account_no || !formData.ifsc) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in Account Number and IFSC',
        variant: 'destructive',
      })
      return
    }

    // For PERMANENT, plan_type should be MONTHLY_SALARY (auto-set)
    // For other types, plan_type is required
    const requiredPlanType = formData.employment_type === 'PERMANENT' ? 'MONTHLY_SALARY' : formData.plan_type
    if (!requiredPlanType || !formData.amount || !formData.valid_from) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in rate plan details (Amount and Start Date are required)',
        variant: 'destructive',
      })
      return
    }

    // Validate contractual salary basis
    if (formData.employment_type === 'CONTRACTUAL' && !formData.working_day_mode) {
      toast({
        title: 'Validation Error',
        description: 'Please select salary basis for contractual employment',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      // Save all details first
      await handleSave()

      // Then submit to HR
      const response = await apiRequest(`/finance/persons/${person.id}/submit-to-hr`, {
        method: 'POST',
      })

      if (response.error) {
        throw new Error(response.error)
      }

      toast({
        title: 'Success',
        description: 'Person submitted to HR successfully',
      })

      onComplete()
      onOpenChange(false)
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err?.error || 'Failed to submit to HR',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent className="max-h-[100dvh] flex flex-col h-[95dvh] sm:max-h-[calc(100vh-48px)] sm:h-auto">
        <DrawerHeader className="flex-shrink-0">
          <DrawerTitle>Complete Finance Processing</DrawerTitle>
          <DrawerDescription>
            {person ? `${person.name} • ${person.mobile}` : 'Loading person details...'}
          </DrawerDescription>
        </DrawerHeader>

        {!person ? (
          <div className="p-8 text-center flex-1">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-400" />
            <p className="text-sm text-gray-500">Loading person details...</p>
          </div>
        ) : (
          <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
            <div className="px-4 pb-24 space-y-6 overflow-y-auto flex-1">
          {/* Assignment Type */}
          <Card>
            <CardHeader>
              <CardTitle>Assignment Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-3">
                <Button
                  type="button"
                  variant={formData.employment_type === 'PERMANENT' ? 'default' : 'outline'}
                  onClick={() => setFormData({ ...formData, employment_type: 'PERMANENT', plan_type: 'MONTHLY_SALARY' })}
                >
                  Permanent
                </Button>
                <Button
                  type="button"
                  variant={formData.employment_type === 'FREELANCER' ? 'default' : 'outline'}
                  onClick={() => setFormData({ ...formData, employment_type: 'FREELANCER' })}
                >
                  Freelancer
                </Button>
                <Button
                  type="button"
                  variant={formData.employment_type === 'CONTRACTUAL' ? 'default' : 'outline'}
                  onClick={() => setFormData({ ...formData, employment_type: 'CONTRACTUAL' })}
                >
                  Contractual
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Company & Employee Code */}
          <Card>
            <CardHeader>
              <CardTitle>Company & Employee Code</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Company</Label>
                <Select
                  value={formData.company_id}
                  onValueChange={(value) => setFormData({ ...formData, company_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select Company" />
                  </SelectTrigger>
                  <SelectContent>
                    {companies.map((company) => (
                      <SelectItem key={company.id} value={company.id.toString()}>
                        {company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {employeeCodePreview && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <Label className="text-sm text-gray-600">Employee Code Preview</Label>
                  <div className="mt-1">
                    <Badge variant="secondary" className="text-lg font-mono">
                      {employeeCodePreview}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Code will be generated automatically on save
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* KYC Details */}
          <Card>
            <CardHeader>
              <CardTitle>KYC Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>
                    Aadhaar <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    value={formData.aadhaar}
                    onChange={(e) => setFormData({ ...formData, aadhaar: e.target.value.replace(/\D/g, '').slice(0, 12) })}
                    placeholder="12 digits"
                    maxLength={12}
                  />
                </div>
                <div className="space-y-2">
                  <Label>
                    PAN <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    value={formData.pan}
                    onChange={(e) => setFormData({ ...formData, pan: e.target.value.toUpperCase().slice(0, 10) })}
                    placeholder="10 characters (uppercase)"
                    maxLength={10}
                    className="uppercase"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Bank Details */}
          <Card>
            <CardHeader>
              <CardTitle>Bank Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>
                    Account Number <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    value={formData.bank_account_no}
                    onChange={(e) => setFormData({ ...formData, bank_account_no: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>
                    IFSC <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    value={formData.ifsc}
                    onChange={(e) => setFormData({ ...formData, ifsc: e.target.value.toUpperCase() })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>
                    Bank Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    value={formData.bank_name}
                    onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                    placeholder="Enter bank name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Branch</Label>
                  <Input
                    value={formData.branch}
                    onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Finance KYC Documents */}
          <Card>
            <CardHeader>
              <CardTitle>Finance KYC Documents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                {/* PAN Card Upload */}
                <div className="space-y-2">
                  <Label>PAN Card</Label>
                  <div className="flex gap-2">
                    <Input
                      type="file"
                      id="pan-upload"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={async (e) => {
                        const file = e.target.files?.[0]
                        if (!file || !person) return
                        
                        setUploadingDoc(true)
                        try {
                          const formDataObj = new FormData()
                          formDataObj.append('file', file)
                          formDataObj.append('stage', 'FINANCE')
                          formDataObj.append('doc_name', 'PAN Card')
                          
                          const response = await apiFetch(`/persons/${person.id}/documents`, {
                            method: 'POST',
                            body: formDataObj,
                          })
                          
                          if (response.ok) {
                            toast({
                              title: 'Success',
                              description: 'PAN Card uploaded successfully',
                            })
                            fetchKycDocuments()
                          } else {
                            const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
                            toast({
                              title: 'Error',
                              description: error.detail || 'Failed to upload PAN Card',
                              variant: 'destructive',
                            })
                          }
                        } catch (err: any) {
                          toast({
                            title: 'Error',
                            description: err.message || 'Failed to upload PAN Card',
                            variant: 'destructive',
                          })
                        } finally {
                          setUploadingDoc(false)
                          e.target.value = ''
                        }
                      }}
                      disabled={uploadingDoc || !person}
                      className="hidden"
                    />
                    <label htmlFor="pan-upload">
                      <Button
                        type="button"
                        variant="outline"
                        disabled={uploadingDoc || !person}
                        asChild
                      >
                        <span>
                          <Upload className="w-4 h-4 mr-2" />
                          {uploadingDoc ? 'Uploading...' : 'Upload PAN Card'}
                        </span>
                      </Button>
                    </label>
                  </div>
                </div>
                
                {/* Aadhaar Card Upload */}
                <div className="space-y-2">
                  <Label>Aadhaar Card</Label>
                  <div className="flex gap-2">
                    <Input
                      type="file"
                      id="aadhaar-upload"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={async (e) => {
                        const file = e.target.files?.[0]
                        if (!file || !person) return
                        
                        setUploadingDoc(true)
                        try {
                          const formDataObj = new FormData()
                          formDataObj.append('file', file)
                          formDataObj.append('stage', 'FINANCE')
                          formDataObj.append('doc_name', 'Aadhaar Card')
                          
                          const response = await apiFetch(`/persons/${person.id}/documents`, {
                            method: 'POST',
                            body: formDataObj,
                          })
                          
                          if (response.ok) {
                            toast({
                              title: 'Success',
                              description: 'Aadhaar Card uploaded successfully',
                            })
                            fetchKycDocuments()
                          } else {
                            const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
                            toast({
                              title: 'Error',
                              description: error.detail || 'Failed to upload Aadhaar Card',
                              variant: 'destructive',
                            })
                          }
                        } catch (err: any) {
                          toast({
                            title: 'Error',
                            description: err.message || 'Failed to upload Aadhaar Card',
                            variant: 'destructive',
                          })
                        } finally {
                          setUploadingDoc(false)
                          e.target.value = ''
                        }
                      }}
                      disabled={uploadingDoc || !person}
                      className="hidden"
                    />
                    <label htmlFor="aadhaar-upload">
                      <Button
                        type="button"
                        variant="outline"
                        disabled={uploadingDoc || !person}
                        asChild
                      >
                        <span>
                          <Upload className="w-4 h-4 mr-2" />
                          {uploadingDoc ? 'Uploading...' : 'Upload Aadhaar Card'}
                        </span>
                      </Button>
                    </label>
                  </div>
                </div>
                
                {/* Cancelled Cheque/Passbook Upload */}
                <div className="space-y-2">
                  <Label>Cancelled Cheque / Passbook</Label>
                  <div className="flex gap-2">
                    <Input
                      type="file"
                      id="cheque-upload"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={async (e) => {
                        const file = e.target.files?.[0]
                        if (!file || !person) return
                        
                        setUploadingDoc(true)
                        try {
                          const formDataObj = new FormData()
                          formDataObj.append('file', file)
                          formDataObj.append('stage', 'FINANCE')
                          formDataObj.append('doc_name', 'Cancelled Cheque')
                          
                          const response = await apiFetch(`/persons/${person.id}/documents`, {
                            method: 'POST',
                            body: formDataObj,
                          })
                          
                          if (response.ok) {
                            toast({
                              title: 'Success',
                              description: 'Cancelled Cheque uploaded successfully',
                            })
                            fetchKycDocuments()
                          } else {
                            const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
                            toast({
                              title: 'Error',
                              description: error.detail || 'Failed to upload Cancelled Cheque',
                              variant: 'destructive',
                            })
                          }
                        } catch (err: any) {
                          toast({
                            title: 'Error',
                            description: err.message || 'Failed to upload Cancelled Cheque',
                            variant: 'destructive',
                          })
                        } finally {
                          setUploadingDoc(false)
                          e.target.value = ''
                        }
                      }}
                      disabled={uploadingDoc || !person}
                      className="hidden"
                    />
                    <label htmlFor="cheque-upload">
                      <Button
                        type="button"
                        variant="outline"
                        disabled={uploadingDoc || !person}
                        asChild
                      >
                        <span>
                          <Upload className="w-4 h-4 mr-2" />
                          {uploadingDoc ? 'Uploading...' : 'Upload Cancelled Cheque'}
                        </span>
                      </Button>
                    </label>
                  </div>
                </div>
              </div>
              
              {kycDocuments.length > 0 && (
                <div className="space-y-2">
                  <Label>Uploaded Documents</Label>
                  <div className="space-y-1">
                    {kycDocuments.map((doc) => (
                      <div key={doc.id} className="flex items-center justify-between p-2 border rounded">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-gray-500" />
                          <span className="text-sm">{doc.doc_name}</span>
                          <Badge variant="outline" className="text-xs">
                            {new Date(doc.created_at).toLocaleDateString()}
                          </Badge>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={async () => {
                            try {
                              const response = await apiFetch(`/finance/documents/${doc.id}/download`)
                              
                              if (response.ok) {
                                const blob = await response.blob()
                                const url = window.URL.createObjectURL(blob)
                                const a = document.createElement('a')
                                a.href = url
                                a.download = doc.doc_name
                                document.body.appendChild(a)
                                a.click()
                                window.URL.revokeObjectURL(url)
                                document.body.removeChild(a)
                              }
                            } catch (err) {
                              toast({
                                title: 'Error',
                                description: 'Failed to download document',
                                variant: 'destructive',
                              })
                            }
                          }}
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Rate / Salary */}
          <Card>
            <CardHeader>
              <CardTitle>
                {formData.employment_type === 'FREELANCER' && 'Manday Rate'}
                {formData.employment_type === 'PERMANENT' && 'Monthly Salary'}
                {formData.employment_type === 'CONTRACTUAL' && 'Contractual Salary'}
                {!formData.employment_type && 'Rate / Salary'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {formData.employment_type === 'FREELANCER' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>
                        Manday Rate <span className="text-red-500">*</span>
                      </Label>
                      <Input
                        type="number"
                        value={formData.amount}
                        onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                        placeholder="0.00"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Plan Type</Label>
                      <Select
                        value={formData.plan_type}
                        onValueChange={(value: any) => setFormData({ ...formData, plan_type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="MANDAY">Manday</SelectItem>
                          <SelectItem value="MANMONTH">Man Month</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>
                        Valid From <span className="text-red-500">*</span>
                      </Label>
                      <Input
                        type="date"
                        value={formData.valid_from}
                        onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Rate Effective To</Label>
                      <Input
                        type="date"
                        value={formData.valid_to}
                        onChange={(e) => setFormData({ ...formData, valid_to: e.target.value })}
                      />
                    </div>
                  </div>
                </>
              )}

              {formData.employment_type === 'PERMANENT' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>
                        Monthly Salary <span className="text-red-500">*</span>
                      </Label>
                      <Input
                        type="number"
                        value={formData.amount}
                        onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                        placeholder="0.00"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Plan Type</Label>
                      <Select
                        value={formData.plan_type || 'MONTHLY_SALARY'}
                        onValueChange={(value: any) => setFormData({ ...formData, plan_type: 'MONTHLY_SALARY' })}
                      >
                        <SelectTrigger>
                          <SelectValue>Monthly Salary</SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="MONTHLY_SALARY">Monthly Salary</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>
                        Start Date <span className="text-red-500">*</span>
                      </Label>
                      <Input
                        type="date"
                        value={formData.valid_from}
                        onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>End Date</Label>
                      <Input
                        type="date"
                        value={formData.valid_to}
                        onChange={(e) => setFormData({ ...formData, valid_to: e.target.value })}
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-500">
                    Note: Corporate policy uses 30/31 day calendar month basis
                  </p>
                </>
              )}

              {formData.employment_type === 'CONTRACTUAL' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>
                        Salary Amount <span className="text-red-500">*</span>
                      </Label>
                      <Input
                        type="number"
                        value={formData.amount}
                        onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                        placeholder="0.00"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>
                        Salary Basis <span className="text-red-500">*</span>
                      </Label>
                      <Select
                        value={formData.working_day_mode}
                        onValueChange={(value) => setFormData({ ...formData, working_day_mode: value })}
                        required
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select salary basis" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="WORKING_26">26 Working Days</SelectItem>
                          <SelectItem value="CALENDAR_30">30 Calendar Days</SelectItem>
                          <SelectItem value="CALENDAR_31">31 Calendar Days</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>
                        Start Date <span className="text-red-500">*</span>
                      </Label>
                      <Input
                        type="date"
                        value={formData.valid_from}
                        onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>End Date</Label>
                      <Input
                        type="date"
                        value={formData.valid_to}
                        onChange={(e) => setFormData({ ...formData, valid_to: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Plan Type</Label>
                    <Select
                      value={formData.plan_type}
                      onValueChange={(value: any) => setFormData({ ...formData, plan_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="MONTHLY_SALARY">Monthly Salary</SelectItem>
                        <SelectItem value="MANMONTH">Man Month</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}

              {!formData.employment_type && (
                <p className="text-sm text-gray-500">Please select employment type first</p>
              )}
            </CardContent>
          </Card>
            </div>

            <DrawerFooter className="flex-shrink-0 bg-white border-t border-gray-200 pt-4 pb-4 shadow-lg">
              <div className="flex gap-2 justify-end">
                <Button
                  variant="outline"
                  onClick={handleSave}
                  disabled={loading || !person}
                >
                  {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                  Save Draft
                </Button>
                <Button
                  onClick={handleSubmitToHR}
                  disabled={loading || !person || !formData.bank_name?.trim() || !hasRequiredKycDocs()}
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                  )}
                  Submit & Send to HR
                </Button>
              </div>
            </DrawerFooter>
          </div>
        )}
      </DrawerContent>
    </Drawer>
  )
}

