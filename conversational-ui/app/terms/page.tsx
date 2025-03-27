import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Use | Umans AI',
  description: 'Terms of Use for Umans AI platform',
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <h1 className="text-3xl font-bold mb-8">Terms of Use</h1>
        
        <div className="prose prose-lg max-w-none prose-invert">
          <p className="text-sm text-gray-400 mb-4">Effective Date: Thursday, 27 March 2025</p>
          
          <div className="space-y-6">
            <p>Welcome to Umans AI, a B2B SaaS platform developed by Umans Tech ("Company," "we," "our," or "us"). These Terms of Use ("Terms") govern your ("Client," "you," or "your") access to and use of the Umans AI services, including our web-based interface, APIs, websites, and related tools (collectively, the "Services").</p>
            
            <p>By creating an account or otherwise using the Services, you agree to be bound by these Terms. If you do not agree, do not access or use the Services.</p>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold">1. Definitions</h3>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Client Data:</strong> Any data, code, text, images, files, or other materials that you upload, submit, or otherwise provide to the Services.</li>
                <li><strong>Output:</strong> Any content generated via the Services in response to or based on Client Data and/or your prompts.</li>
                <li><strong>LLM Provider:</strong> The third-party provider of large language model services used within Umans AI.</li>
                <li><strong>Authorized Users:</strong> Individuals authorized by you to access and use the Services under your account.</li>
              </ul>

              <h3 className="text-xl font-semibold">2. Acceptance and Modification of Terms</h3>
              <p>These Terms form a legally binding agreement between you and Umans Tech upon the earlier of:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Clicking "I agree" (or similar)</li>
                <li>Your use of the Services</li>
              </ul>

              <h3 className="text-xl font-semibold">3. The Services</h3>
              <p>Umans AI allows Clients to:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Upload data (including code, documents, or other information)</li>
                <li>Use AI-driven features to gain insights</li>
                <li>Generate code suggestions</li>
                <li>Produce text-based Output</li>
              </ul>

              <h3 className="text-xl font-semibold">4. Registration and Accounts</h3>
              <ul className="list-disc pl-6 space-y-2">
                <li>You must create an account to access the Services</li>
                <li>You are responsible for safeguarding your account credentials</li>
                <li>You must ensure your Authorized Users comply with these Terms</li>
              </ul>

              <h3 className="text-xl font-semibold">5. Client Data and Output</h3>
              <ul className="list-disc pl-6 space-y-2">
                <li>You retain all rights and ownership in your Client Data</li>
                <li>Subject to payment of applicable fees, you own the Output generated specifically for you</li>
                <li>You grant Umans Tech and its LLM Provider a non-exclusive license to process your data</li>
              </ul>
            </div>

            <div className="mt-8 text-sm text-gray-400">
              <p>Last Updated: 27 March 2025</p>
              <p className="mt-2">For any questions, please contact us at:</p>
              <p>Umans Tech<br />
              14 Rue de Sévigné<br />
              92120 Montrouge, France<br />
              Email: contact@umans.tech</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 