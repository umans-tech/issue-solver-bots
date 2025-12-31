'use client';

import { useState, useEffect } from 'react';
import { usePostHog } from 'posthog-js/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2 } from 'lucide-react';

export function EnvsWaitlistForm() {
  const posthog = usePostHog();
  const [formData, setFormData] = useState({
    email: '',
    role: '',
    goal: '',
    repos_count: '',
    need_vpc: '',
    pricing_expectation: '',
    repo_link: '',
  });
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [hasFocused, setHasFocused] = useState(false);

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleFocus = () => {
    if (!hasFocused) {
        setHasFocused(true);
        posthog?.capture('form_started', {
            waitlist_id: 'envs',
            page_path: window.location.pathname
        });
    }
  };

  useEffect(() => {
    const handleUnload = () => {
        if (hasFocused && status !== 'success') {
           posthog?.capture('form_abandoned', {
               waitlist_id: 'envs',
               page_path: window.location.pathname
           });
        }
    }
    return handleUnload;
  }, [hasFocused, status, posthog]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('submitting');
    setErrorMessage('');

    try {
      const searchParams = new URLSearchParams(window.location.search);
      const utm = {
        source: searchParams.get('utm_source') || undefined,
        medium: searchParams.get('utm_medium') || undefined,
        campaign: searchParams.get('utm_campaign') || undefined,
        content: searchParams.get('utm_content') || undefined,
        term: searchParams.get('utm_term') || undefined,
      };

      const res = await fetch('/api/waitlist/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          waitlist_id: 'envs',
          email: formData.email,
          role: formData.role || undefined,
          goal: formData.goal || undefined,
          repos_count: formData.repos_count || undefined,
          need_vpc: formData.need_vpc ? formData.need_vpc === 'yes' : undefined,
          pricing_expectation: formData.pricing_expectation || undefined,
          repo_link: formData.repo_link || undefined,
          utm,
          referrer: document.referrer,
          page_path: window.location.pathname,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      setStatus('success');
      posthog?.capture('submit_waitlist_success', {
          waitlist_id: 'envs',
          page_path: window.location.pathname
      });

    } catch (error: any) {
      console.error(error);
      setStatus('error');
      setErrorMessage(error.message);
    }
  };

  if (status === 'success') {
    return (
      <div className="text-center p-8 bg-muted/30 rounded-lg border border-border animate-in fade-in duration-500">
        <h3 className="text-2xl font-bold mb-2">You're on the list!</h3>
        <p className="text-muted-foreground mb-6">
          We'll reach out as soon as a spot opens up.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-md mx-auto text-left" onFocus={handleFocus}>
      <div className="space-y-2">
        <Label htmlFor="email">Work Email</Label>
        <Input
          id="email"
          type="email"
          required
          placeholder="name@company.com"
          value={formData.email}
          onChange={(e) => handleChange('email', e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="role">Role</Label>
        <Select onValueChange={(val) => handleChange('role', val)}>
          <SelectTrigger id="role">
            <SelectValue placeholder="Select your role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="engineer">Software Engineer</SelectItem>
            <SelectItem value="platform">Platform/DevOps</SelectItem>
            <SelectItem value="manager">Engineering Manager</SelectItem>
            <SelectItem value="founder">Founder/CTO</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="goal">What are you trying to run?</Label>
        <Textarea
          id="goal"
          placeholder="e.g. A coding agent that runs tests on every PR"
          value={formData.goal}
          onChange={(e) => handleChange('goal', e.target.value)}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="repos_count">Repos count</Label>
          <Select onValueChange={(val) => handleChange('repos_count', val)}>
            <SelectTrigger id="repos_count">
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1</SelectItem>
              <SelectItem value="2-5">2-5</SelectItem>
              <SelectItem value="6-20">6-20</SelectItem>
              <SelectItem value="20+">20+</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="need_vpc">Need VPC / on-prem?</Label>
          <Select onValueChange={(val) => handleChange('need_vpc', val)}>
            <SelectTrigger id="need_vpc">
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="yes">Yes</SelectItem>
              <SelectItem value="no">No</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="pricing_expectation">Pricing expectation (optional)</Label>
        <Select onValueChange={(val) => handleChange('pricing_expectation', val)}>
          <SelectTrigger id="pricing_expectation">
            <SelectValue placeholder="Select preference" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="per_hour">Per sandbox hour</SelectItem>
            <SelectItem value="per_repo">Per repo</SelectItem>
            <SelectItem value="per_seat">Per seat</SelectItem>
            <SelectItem value="flat_team">Per team (flat monthly)</SelectItem>
            <SelectItem value="not_sure">Not sure yet</SelectItem>
          </SelectContent>
        </Select>
      </div>

       <div className="space-y-2">
        <Label htmlFor="repo_link">Public repo link (optional)</Label>
        <Input
          id="repo_link"
          type="url"
          placeholder="https://github.com/..."
          value={formData.repo_link}
          onChange={(e) => handleChange('repo_link', e.target.value)}
        />
      </div>

      {status === 'error' && (
        <p className="text-red-500 text-sm">{errorMessage}</p>
      )}

      <Button type="submit" className="w-full" disabled={status === 'submitting'}>
        {status === 'submitting' ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Joining...
          </>
        ) : (
          'Join the waitlist'
        )}
      </Button>
    </form>
  );
}