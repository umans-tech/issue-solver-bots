import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy | Umans AI',
  description: 'Privacy Policy for Umans AI platform',
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>

        <div className="prose prose-lg max-w-none prose-invert">
          <p className="text-sm text-gray-400 mb-4">
            Effective Date: Thursday, 27 March 2025
          </p>

          <div className="space-y-6">
            <p>
              Umans AI ("we," "us," "our") respects your privacy. This Privacy
              Policy describes how we collect, use, and share personal data when
              you use the Umans AI platform and related services (the
              "Services").
            </p>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold">1. Who We Are</h3>
              <p>
                We are Umans AI, located at 14 Rue de Sévigné, 92120 Montrouge,
                France. You can reach us at contact@umans.tech.
              </p>

              <h3 className="text-xl font-semibold">
                2. Personal Data We Collect
              </h3>
              <ul className="list-disc pl-6 space-y-2">
                <li>
                  <strong>Account Information:</strong> Name, email address,
                  company name, billing information, and other contact details.
                </li>
                <li>
                  <strong>Client Data:</strong> The data, code, or content you
                  submit to the Services.
                </li>
                <li>
                  <strong>Automatically Collected Data:</strong> Log data,
                  cookies, and usage information.
                </li>
                <li>
                  <strong>Information from Third Parties:</strong> Data received
                  from service providers.
                </li>
              </ul>

              <h3 className="text-xl font-semibold">3. How We Use Your Data</h3>
              <p>We process personal data for:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Providing and Improving Services</li>
                <li>Data Handling with LLM Provider</li>
                <li>Security and Fraud Prevention</li>
                <li>Legal Compliance</li>
                <li>Communications</li>
              </ul>

              <h3 className="text-xl font-semibold">
                4. Your Rights under GDPR
              </h3>
              <p>You have certain rights regarding your personal data:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Access: Request a copy of your personal data</li>
                <li>Rectification: Correct inaccurate or incomplete data</li>
                <li>Erasure: Request deletion of your data</li>
                <li>Restriction: Limit the processing of your data</li>
                <li>Objection: Object to certain processing</li>
                <li>Portability: Request transfer of your data</li>
              </ul>
            </div>

            <div className="mt-8 text-sm text-gray-400">
              <p>Last Updated: 27 March 2025</p>
              <p className="mt-2">For any questions, please contact us at:</p>
              <p>
                Umans AI
                <br />
                14 Rue de Sévigné
                <br />
                92120 Montrouge, France
                <br />
                Email: contact@umans.tech
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
