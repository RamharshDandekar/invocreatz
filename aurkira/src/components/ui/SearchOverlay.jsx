'use client';

import React, { useState, useEffect, useRef } from 'react';
import { XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';
import Image from 'next/image';
import { getTrendingProducts, getPopularSearches } from '../lib/api';

const SearchOverlay = ({ onClose }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [trendingProducts, setTrendingProducts] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const searchInputRef = useRef(null);
    const [popularSearches, setPopularSearches] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            setError(null);

            try {
                const trendingData = await getTrendingProducts();
                setTrendingProducts(trendingData);

                const popularSearchesData = await getPopularSearches();
                setPopularSearches(popularSearchesData);
            } catch (err) {
                console.error("Error fetching data:", err);
                setError("Failed to load data. Please try again later.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();

        if (searchInputRef.current) {
            searchInputRef.current.focus();
        }
    }, []);


    const handleSearch = async (e) => {
        setSearchTerm(e.target.value);
    };

    return (
        <div className="fixed top-0 left-0 w-full h-full bg-white z-50 overflow-y-auto">
            <div className="container mx-auto py-12 px-4 sm:px-6 lg:px-8">
                {/* Search Input */}
                <div className="flex items-center mb-8 relative rounded-lg shadow-md">
                    <input
                        type="text"
                        placeholder="What are you looking for?"
                        className="w-full rounded-l-lg border-0 py-2.5 pr-16 text-gray-900 placeholder:text-gray-500 focus:ring-2 focus:ring-purple-500 sm:text-sm sm:leading-6 pl-5 outline-none"
                        value={searchTerm}
                        onChange={handleSearch}
                        ref={searchInputRef}
                    />
                    <button className="absolute right-14 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700" type="submit">
                        <MagnifyingGlassIcon className="h-5 w-5" aria-hidden="true" />
                    </button>
                    <button onClick={onClose} className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700">
                        <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                    </button>
                </div>

                {/* Popular Searches */}
                <div className="mb-10">
                    <h2 className="text-lg font-semibold mb-5 text-gray-700">Popular Searches</h2>
                    <div className="flex flex-wrap gap-3">
                        {popularSearches && popularSearches.map((search, index) => (
                            <button key={index} className="bg-purple-100 text-purple-700 rounded-full px-4 py-2 text-sm hover:bg-purple-200 transition duration-200">{search}</button>
                        ))}
                    </div>
                </div>

                {/* Trending Now */}
                <div>
                    <h2 className="text-lg font-semibold mb-5 flex items-center text-gray-700">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-6 h-6 mr-2 text-purple-500">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                        </svg>
                        Trending Now
                    </h2>
                    {isLoading ? (
                        <div className="text-gray-600">Loading trending products...</div>
                    ) : error ? (
                        <div className="text-red-500">Error: {error}</div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                            {trendingProducts.map((item) => (
                                <div key={item.id} className="rounded-lg shadow-md overflow-hidden hover:shadow-lg transition duration-300">
                                    <Link href={`/shop/${item.id}`} className="block">
                                        <div className="relative aspect-w-4 aspect-h-3">
                                            <Image
                                                src={item.imageUrl}
                                                alt={item.name}
                                                layout="fill"
                                                objectFit="cover"
                                                className="transition-transform duration-300 group-hover:scale-105"
                                            />
                                        </div>
                                        <div className="p-4">
                                            <h3 className="text-sm font-semibold text-gray-800 line-clamp-2">{item.name}</h3>
                                            <p className="text-gray-600 mt-1">₹{item.price}</p>
                                            {item.discount && <p className="text-red-600 mt-1">-{item.discount}% Off</p>}
                                        </div>
                                    </Link>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SearchOverlay;