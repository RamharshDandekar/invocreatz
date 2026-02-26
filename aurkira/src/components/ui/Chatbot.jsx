'use client'

import React, { useState, useEffect, useRef } from 'react';
import { XMarkIcon, ChatBubbleOvalLeftEllipsisIcon, PaperAirplaneIcon } from '@heroicons/react/24/solid';
import axios from 'axios';

const Chatbot = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [userInput, setUserInput] = useState('');
    const chatContainerRef = useRef(null);
    const [initialPromptShown, setInitialPromptShown] = useState(false);
    const [showInitialPopup, setShowInitialPopup] = useState(false);
    const [isClosing, setIsClosing] = useState(false);
    const chatbotButtonRef = useRef(null);
    const [origin, setOrigin] = useState({ x: 0, y: 0 });
    const [firstOpen, setFirstOpen] = useState(true);
    const [sessionId, setSessionId] = useState('');
    const [initialQuery, setInitialQuery] = useState('');
    const [isLoadingInitialMessage, setIsLoadingInitialMessage] = useState(false);  // Loading state

    const API_BASE_URL_ai = process.env.NEXT_PUBLIC_API_BASE_URL_ai;

    const generateUUID = () => {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    };

    const getSessionId = () => {
        let storedSessionId = localStorage.getItem('sessionId');
        if (!storedSessionId) {
            storedSessionId = generateUUID();
            localStorage.setItem('sessionId', storedSessionId);
        }
        return storedSessionId;
    };

    useEffect(() => {
        const initialSessionId = getSessionId();
        setSessionId(initialSessionId);
    }, []);

    useEffect(() => {
        const handleLogout = () => {
            localStorage.removeItem('chatbotMessages');
            localStorage.removeItem('sessionId');
            setMessages([]);
            setSessionId('');
        };
        window.addEventListener('user-logout', handleLogout);
        return () => window.removeEventListener('user-logout', handleLogout);
    }, []);

    useEffect(() => {
        try {
            localStorage.setItem('chatbotMessages', JSON.stringify(messages));
        } catch (err) {
            console.error('Error saving to localStorage:', err);
        }
    }, [messages]);

    useEffect(() => {
        try {
            const stored = localStorage.getItem('chatbotMessages');
            if (stored) {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    setMessages(parsed);
                    setInitialPromptShown(true);
                }
            }
        } catch (err) {
            console.error('Failed to load messages:', err);
        }
    }, []);

    useEffect(() => {
        const fetchInitialMessage = async () => {
            setIsLoadingInitialMessage(true); // Set loading to true
            try {
                let initialQuery = "general";
                const pathname = window.location.pathname;
                if (pathname.includes("saree")) {
                    initialQuery = "saree";
                } else if (pathname.includes("dress")) {
                    initialQuery = "dress";
                } else if (pathname.includes("shirt")) {
                    initialQuery = "shirt";
                } else if (pathname.includes("pant")) {
                    initialQuery = "pant";
                }

                setInitialQuery(initialQuery);

                const response = await axios.post(`${API_BASE_URL_ai}/chat`, {
                    message: '',
                    currentPath: pathname,
                    sessionId: sessionId,
                    initialQuery: initialQuery
                });

                if (response.data && response.data.reply) {
                    setMessages([{ sender: 'bot', text: response.data.reply }]);
                    if (response.data.sessionId) {
                        localStorage.setItem('sessionId', response.data.sessionId);
                        setSessionId(response.data.sessionId);
                    }
                } else {
                    console.error("Invalid response format:", response);
                    setMessages([{ sender: 'bot', text: "Sorry, I couldn't load an initial message." }]);
                }

            } catch (error) {
                console.error('Error fetching welcome message:', error);
                setMessages([{ sender: 'bot', text: 'Welcome, what’s on your mind today?' }]);
            } finally {
                setInitialPromptShown(true);
                setShowInitialPopup(true);
                setIsLoadingInitialMessage(false);  // Set loading to false
            }
        };

        if (!initialPromptShown && sessionId) {
            const timer = setTimeout(() => {
                fetchInitialMessage();
            }, 1000); //Reduced timer to 1 sec

            return () => clearTimeout(timer);
        }
    }, [initialPromptShown, API_BASE_URL_ai, sessionId]);

    // NEW CODE BLOCK STARTS HERE
    useEffect(() => {
        const handleProductAdded = async (event) => {
            const product = event.detail;
            // Basic validation to ensure we have the needed product data
            if (!product || !product.name || !product.category || !product.category.name) {
                console.error("Chatbot: Invalid product data received in 'product-added-to-cart' event.", product);
                return;
            };

            // Force the chat window to open
            if (!isOpen) {
                toggleChat();
            }

            // Display a temporary "thinking" message to the user
            const thinkingMessage = { sender: 'bot', text: `Great choice on the ${product.name}! Finding some recommendations...` };
            setMessages(prev => [...prev, thinkingMessage]);

            try {
                // Call the new backend endpoint for cross-selling
                const response = await axios.post(`${API_BASE_URL_ai}/product-added`, {
                    sessionId: sessionId,
                    productName: product.name,
                    productCategory: product.category.name
                });

                if (response.data && response.data.reply) {
                    const botMessage = { sender: 'bot', text: response.data.reply };
                    // Replace the "thinking" message with the real AI-generated response
                    setMessages(prev => [...prev.slice(0, -1), botMessage]);
                } else {
                     throw new Error("Invalid response format from server");
                }
            } catch (error) {
                console.error('Error fetching cross-sell suggestions:', error);
                const errorMessage = { sender: 'bot', text: "Sorry, I couldn't fetch recommendations right now." };
                // Replace the "thinking" message with an error message
                setMessages(prev => [...prev.slice(0, -1), errorMessage]);
            }
        };

        // Listen for the global event dispatched from other components
        window.addEventListener('product-added-to-cart', handleProductAdded);

        // Cleanup the event listener when the component unmounts
        return () => {
            window.removeEventListener('product-added-to-cart', handleProductAdded);
        };
    }, [sessionId, API_BASE_URL_ai, isOpen]); // Rerun if sessionId or isOpen state changes
    // NEW CODE BLOCK ENDS HERE

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const handleInputChange = (e) => setUserInput(e.target.value);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!userInput.trim()) return;

        const userMessage = { sender: 'user', text: userInput };
        setMessages(prev => [...prev, userMessage]);
        setUserInput('');

        try {
            const response = await axios.post(`${API_BASE_URL_ai}/chat`, {
                message: userInput,
                currentPath: window.location.pathname,
                sessionId: sessionId
            });
            if (response.data && response.data.reply) {
                const botMessage = { sender: 'bot', text: response.data.reply };
                setMessages(prev => [...prev, botMessage]);
                if (response.data.sessionId) {
                    localStorage.setItem('sessionId', response.data.sessionId);
                    setSessionId(response.data.sessionId);
                }
            } else {
                console.error("Invalid response format:", response);
                setMessages(prev => [...prev, { sender: 'bot', text: "Sorry, I couldn't process your message." }]);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, { sender: 'bot', text: "Sorry, I'm having trouble connecting to the server. Please try again later." }]);
        }
    };

    const toggleChat = () => {
        if (chatbotButtonRef.current) {
            const rect = chatbotButtonRef.current.getBoundingClientRect();
            const newOrigin = {
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
            };
            setOrigin(newOrigin);
        }

        if (isOpen) {
            setIsClosing(true);
            setTimeout(() => {
                setIsOpen(false);
                setIsClosing(false);
            }, 300);
        } else {
            setIsOpen(true);
            setInitialPromptShown(true);
            setShowInitialPopup(false);
        }
    };

    const handleDismissPopup = () => {
        setShowInitialPopup(false);
    };

    const chatbotStyle = {
        transformOrigin: `${origin.x}px ${origin.y}px`,
    };

    const transitionClass = firstOpen ? ' apply-transition' : '';

    return (
        <div className="fixed bottom-5 right-5 z-50">
            {/* Initial preview popup with dismiss button */}
            {!isOpen && showInitialPopup && messages.length > 0 && (
                <div className="absolute bottom-16 right-0 bg-white text-gray-800 p-4 rounded-xl shadow-xl border border-purple-300 w-72 animate-fade-in">
                    <div className="flex justify-between items-start">
                        <p className="text-sm pr-2 flex-grow cursor-pointer" onClick={toggleChat}>
                            {messages[0].text}
                        </p>
                        <button onClick={handleDismissPopup} className="text-gray-400 hover:text-gray-600">
                            <XMarkIcon className="h-5 w-5" />
                        </button>
                    </div>
                </div>
            )}

            {isOpen && (
                <div
                    className={`w-full sm:w-96 max-w-full h-[500px] bg-white border border-gray-300 rounded-3xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300 ease-in-out ${isClosing ? 'scale-0 opacity-0' : 'scale-100 opacity-100'}`}
                    style={chatbotStyle}
                    onAnimationEnd={() => setFirstOpen(false)}
                >
                    <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-5 py-4 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <ChatBubbleOvalLeftEllipsisIcon className="h-6 w-6" />
                            <span className="font-semibold">Chatbot</span>
                        </div>
                        <button onClick={toggleChat} className="text-white hover:text-gray-200">
                            <XMarkIcon className="h-6 w-6 cursor-pointer" />
                        </button>
                    </div>

                    <div ref={chatContainerRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3 bg-gray-50">
                        {isLoadingInitialMessage && (  // Display loading indicator
                            <div className="p-3 rounded-2xl max-w-[80%] bg-purple-100 text-gray-900">
                                Loading...
                            </div>
                        )}
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`p-3 rounded-2xl max-w-[80%] ${msg.sender === 'user'
                                    ? 'ml-auto bg-pink-100 text-gray-900'
                                    : 'bg-purple-100 text-gray-900'
                                    }`}
                            >
                                {msg.text}
                            </div>
                        ))}
                    </div>

                    <form onSubmit={handleSubmit} className="p-3 border-t border-gray-200 flex space-x-2 bg-white">
                        <input
                            type="text"
                            value={userInput}
                            onChange={handleInputChange}
                            placeholder="Type a message..."
                            className="flex-grow px-4 py-2 rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-400"
                        />
                        <button
                            type="submit"
                            className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-full cursor-pointer"
                        >
                            <PaperAirplaneIcon className="h-5 w-5" />
                        </button>
                    </form>
                </div>
            )}

            {!isOpen && (
                <button
                    ref={chatbotButtonRef}
                    onClick={toggleChat}
                    className="p-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-full shadow-lg transition-all duration-300"
                    style={{ transitionTimingFunction: 'ease' }}
                >
                    <ChatBubbleOvalLeftEllipsisIcon className="h-6 w-6 cursor-pointer" />
                </button>
            )}
        </div>
    );
};

export default Chatbot;