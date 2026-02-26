"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { FaInstagram, FaTwitter, FaGithub, FaLinkedin } from 'react-icons/fa'; // React Icons

const Footer = () => {
    const [email, setEmail] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [subscriptionMessage, setSubscriptionMessage] = useState('');
    const handleEmailChange = (e) => {
        setEmail(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setSubscriptionMessage(''); // Clear previous messages

        try {
            const response = await fetch('/api/subscribe', { // Assumes api/subscribe exists
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (response.ok) {
                setSubscriptionMessage('Successfully subscribed!');
            } else {
                setSubscriptionMessage(`Subscription failed: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Subscription error:', error);
            setSubscriptionMessage('Subscription failed: An unexpected error occurred.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <footer className="bg-purple-100 border-t border-gray-200 py-12">
            <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    {/* Logo and Copyright */}
                    <div className="md:col-span-1">
                        <Link href="/" className="flex items-center text-lg font-semibold text-gray-800">
                            <Image
                                src="/logo.jpeg" // Replace with your logo
                                alt="AURKIRA"
                                className="h-8 w-auto mr-2"
                                width={32}
                                height={32}
                            />
                            AURKIRA
                        </Link>
                        <p className="text-gray-500 mt-4 text-sm">© 2024 AURKIRA, Inc. All rights reserved.</p>
                    </div>

                    {/* Solutions */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-3">Solutions</h3>
                        <ul className="text-sm text-gray-500 space-y-2">
                            <li><Link href="#">Marketing</Link></li>
                            <li><Link href="#">Analytics</Link></li>
                            <li><Link href="#">Automation</Link></li>
                            <li><Link href="#">Commerce</Link></li>
                            <li><Link href="#">Insights</Link></li>
                        </ul>
                    </div>

                    {/* Support */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-3">Support</h3>
                        <ul className="text-sm text-gray-500 space-y-2">
                            <li><Link href="#">Submit Ticket</Link></li>
                            <li><Link href="#">Documentation</Link></li>
                            <li><Link href="#">Guides</Link></li>
                        </ul>
                    </div>

                    {/* Company */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-3">Company</h3>
                        <ul className="text-sm text-gray-500 space-y-2">
                            <li><Link href="#">About</Link></li>
                            <li><Link href="#">Blog</Link></li>
                            <li><Link href="#">Jobs</Link></li>
                            <li><Link href="#">Press</Link></li>
                        </ul>
                    </div>
                </div>

                {/* Newsletter Subscription */}
                <div className="md:flex items-center justify-between border-t border-gray-200 pt-8 pb-4">
                    <div className="mb-4 md:mb-0">
                        <h4 className="text-sm font-semibold text-gray-700">Subscribe to our newsletter</h4>
                        <p className="text-gray-500 text-sm">The latest news, articles, and resources, sent to your inbox weekly.</p>
                    </div>
                    <form onSubmit={handleSubmit} className="flex flex-col md:flex-row items-center">
                        <input
                            type="email"
                            placeholder="Enter your email"
                            className="w-full md:w-auto rounded-md bg-gray-100 border-gray-300 shadow-sm focus:ring-purple-500 focus:border-purple-500 text-sm px-4 py-2 outline-none"
                            value={email}
                            onChange={handleEmailChange}
                            required
                        />
                        <button
                            type="submit"
                            className="bg-purple-500 text-white rounded-md px-5 py-2.5 ml-0 md:ml-3 mt-3 md:mt-0 text-sm font-medium hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? 'Subscribing...' : 'Subscribe'}
                        </button>
                    </form>
                </div>
                  {subscriptionMessage && (
                  <p
                    className={`mt-3 text-sm ${
                      subscriptionMessage.startsWith('Successfully')
                        ? 'text-green-500'
                        : 'text-red-500'
                    }`}
                  >
                    {subscriptionMessage}
                  </p>
                )}

                {/* Social Icons */}
                <div className="flex justify-center md:justify-start mt-8">
                    <Link href="#" className="text-gray-400 hover:text-gray-500 transition-colors duration-200 mr-4"><FaInstagram className="h-5 w-5" /></Link>
                    <Link href="#" className="text-gray-400 hover:text-gray-500 transition-colors duration-200 mr-4"><FaTwitter className="h-5 w-5" /></Link>
                    <Link href="https://github.com/ramharsh-aidev" className="text-gray-400 hover:text-gray-500 transition-colors duration-200 mr-4"><FaGithub className="h-5 w-5" /></Link>
                    <Link href="https://www.linkedin.com/in/ramharsh-sanjay-dandekar" className="text-gray-400 hover:text-gray-500 transition-colors duration-200"><FaLinkedin className="h-5 w-5" /></Link>
                </div>
            </div>
        </footer>
    );
};

export default Footer;