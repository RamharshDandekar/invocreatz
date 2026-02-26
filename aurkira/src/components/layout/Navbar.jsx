'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogBackdrop, DialogPanel, Popover, PopoverButton, PopoverGroup, PopoverPanel } from '@headlessui/react';
import { Bars3Icon, ShoppingBagIcon, XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';
import Image from 'next/image';
import { UserButton, SignInButton, useUser } from "@clerk/nextjs";
import SearchOverlay from '../ui/SearchOverlay';
import { getTrendingProducts } from '../lib/api';

// Improved Category Data Structure
const navigation = {
    categories: [
        {
            id: 'women',
            name: 'Women',
            featured: [
                { name: 'New Arrivals', href: '/shop?category=women&new=true' },
                { name: 'Basic Tees', href: '/shop?category=women&type=tee' },
            ],
            subcategories: [
                {
                    id: 'clothing',
                    name: 'Clothing',
                    items: [
                        { name: 'Tops', href: '/shop?category=women&clothing=tops' },
                        { name: 'Dresses', href: '/shop?category=women&clothing=dresses' },
                        { name: 'Jeans & Jeggings', href: '/shop?category=women&clothing=jeans' }, // more specific name
                        { name: 'Skirts', href: '/shop?category=women&clothing=skirts' },
                        { name: 'Trousers & Pants', href: '/shop?category=women&clothing=pants' },
                        { name: 'Sweaters & Cardigans', href: '/shop?category=women&clothing=sweaters' },
                        { name: 'T-Shirts', href: '/shop?category=women&clothing=t-shirts' },
                        { name: 'Jackets & Coats', href: '/shop?category=women&clothing=jackets' },
                        { name: 'Lingerie & Sleepwear', href: '/shop?category=women&clothing=lingerie' },
                        { name: 'Browse All', href: '/shop?category=women&clothing=clothing' }, // Generic all clothing route
                    ],
                },
                {
                    id: 'footwear',
                    name: 'Footwear',
                    items: [
                        { name: 'Heels', href: '/shop?category=women&footwear=heels' },
                        { name: 'Sandals', href: '/shop?category=women&footwear=sandals' },
                        { name: 'Sneakers & Athletic Shoes', href: '/shop?category=women&footwear=sneakers' },
                        { name: 'Boots', href: '/shop?category=women&footwear=boots' },
                        { name: 'Flats', href: '/shop?category=women&footwear=flats' },
                        { name: 'Browse All', href: '/shop?category=women&footwear=footwear' },
                    ],
                },
                {
                    id: 'accessories',
                    name: 'Accessories',
                    items: [
                        { name: 'Watches', href: '/shop?category=women&accessories=watches' },
                        { name: 'Handbags', href: '/shop?category=women&accessories=handbags' }, //More appropriate name
                        { name: 'Jewellery', href: '/shop?category=women&accessories=jewellery' },
                        { name: 'Sunglasses', href: '/shop?category=women&accessories=sunglasses' },
                        { name: 'Hats & Caps', href: '/shop?category=women&accessories=hats' },
                        { name: 'Belts', href: '/shop?category=women&accessories=belts' },
                        { name: 'Scarves & Wraps', href: '/shop?category=women&accessories=scarves' },
                        { name: 'Browse All', href: '/shop?category=women&accessories=accessories' },
                    ],
                },
            ],
        },
        {
            id: 'men',
            name: 'Men',
            featured: [
                { name: 'New Arrivals', href: '/shop?category=men&new=true' },
                { name: 'Graphic Tees', href: '/shop?category=men&type=tee' },
            ],
            subcategories: [
                {
                    id: 'clothing',
                    name: 'Clothing',
                    items: [
                        { name: 'Tops', href: '/shop?category=men&clothing=tops' },
                        { name: 'Jeans', href: '/shop?category=men&clothing=jeans' },
                        { name: 'Trousers & Chinos', href: '/shop?category=men&clothing=pants' },
                        { name: 'Sweaters & Hoodies', href: '/shop?category=men&clothing=sweaters' },
                        { name: 'T-Shirts', href: '/shop?category=men&clothing=t-shirts' },
                        { name: 'Jackets & Coats', href: '/shop?category=men&clothing=jackets' },
                        { name: 'Activewear', href: '/shop?category=men&clothing=activewear' },
                        { name: 'Browse All', href: '/shop?category=men&clothing=clothing' },
                    ],
                },
                {
                    id: 'footwear',
                    name: 'Footwear',
                    items: [
                        { name: 'Casual Shoes', href: '/shop?category=men&footwear=casual' },
                        { name: 'Sneakers', href: '/shop?category=men&footwear=sneakers' },
                        { name: 'Boots', href: '/shop?category=men&footwear=boots' },
                        { name: 'Formal Shoes', href: '/shop?category=men&footwear=formal' },
                        { name: 'Sandals & Flip-Flops', href: '/shop?category=men&footwear=sandals' },
                        { name: 'Browse All', href: '/shop?category=men&footwear=footwear' },
                    ],
                },
                {
                    id: 'accessories',
                    name: 'Accessories',
                    items: [
                        { name: 'Watches', href: '/shop?category=men&accessories=watches' },
                        { name: 'Wallets', href: '/shop?category=men&accessories=wallets' },
                        { name: 'Bags', href: '/shop?category=men&accessories=bags' },
                        { name: 'Sunglasses', href: '/shop?category=men&accessories=sunglasses' },
                        { name: 'Hats & Caps', href: '/shop?category=men&accessories=hats' },
                        { name: 'Belts', href: '/shop?category=men&accessories=belts' },
                        { name: 'Browse All', href: '/shop?category=men&accessories=accessories' },
                    ],
                },
            ],
        },
    ],
    pages: [
        { name: 'About-Us', href: '/about' },
        { name: 'Store', href: '/shop' },
    ],
}

const promotionalMessage = "Get free delivery on orders over $100";


// Reusable Components
const CategoryMenu = ({ category, trendingProducts }) => {
    const getTrendingForCategory = (categoryName) => {
        return trendingProducts?.filter(product => product.category === categoryName).slice(0, 2) || []; // Use optional chaining
    };

    return (
        <Popover className="flex">
            {({ open }) => (
                <>
                    <div className="relative flex">
                        <PopoverButton
                            className={`relative z-10 -mb-px flex items-center border-b-2 border-transparent pt-px text-sm font-medium focus:outline-none transition-colors duration-200 ease-out ${open ? 'text-purple-600 border-purple-500' : 'text-gray-700 hover:text-purple-600 hover:border-purple-500'
                                }`}
                            onMouseEnter={(e) => { e.currentTarget.click() }}
                            onMouseLeave={(e) => { e.currentTarget.blur() }}
                        >
                            {category.name}
                        </PopoverButton>
                    </div>
                    <PopoverPanel
                        transition
                        className="absolute inset-x-0 top-full text-sm text-gray-500 transition data-closed:opacity-0 data-enter:duration-200 data-enter:ease-out data-leave:duration-150 data-leave:ease-in"
                        onMouseEnter={(e) => { e.currentTarget.focus() }}
                        onMouseLeave={(e) => { e.currentTarget.blur() }}
                    >
                        <div aria-hidden="true" className="absolute inset-0 top-1/2 bg-white shadow-sm" />
                        <div className="relative bg-white">
                            <div className="mx-auto max-w-7xl px-8">
                                <div className="grid grid-cols-2 gap-x-8 gap-y-10 py-16">
                                    <div className="col-start-2 grid grid-cols-2 gap-x-8">
                                        {trendingProducts ? (
                                            getTrendingForCategory(category.name).map((item) => (
                                                <div key={item.name} className="group relative text-base sm:text-sm">
                                                    <Image
                                                        src={item.imageSrc}
                                                        alt={item.imageAlt}
                                                        className="aspect-square w-full rounded-lg bg-gray-100 object-cover group-hover:opacity-75"
                                                        width={500}
                                                        height={500}
                                                        quality={75}
                                                    />
                                                    <Link href={item.href} className="mt-6 block font-medium text-gray-900">
                                                        <span aria-hidden="true" className="absolute inset-0 z-10" />
                                                        {item.name}
                                                    </Link>
                                                    <p aria-hidden="true" className="mt-1">
                                                        Shop now
                                                    </p>
                                                </div>
                                            ))
                                        ) : (
                                            <div>Loading trending products...</div>
                                        )}
                                    </div>
                                    <div className="row-start-1 grid grid-cols-3 gap-x-8 gap-y-10 text-sm">
                                        {category.subcategories.map((subcategory) => (
                                            <div key={subcategory.name}>
                                                <p id={`${subcategory.name}-heading`} className="font-medium text-gray-900">
                                                    {subcategory.name}
                                                </p>
                                                <ul
                                                    role="list"
                                                    aria-labelledby={`${subcategory.name}-heading`}
                                                    className="mt-6 space-y-6 sm:mt-4 sm:space-y-4">
                                                    {subcategory.items.map((item) => (
                                                        <li key={item.name} className="flex">
                                                            <Link href={item.href} className="hover:text-purple-600">
                                                                {item.name}
                                                            </Link>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </PopoverPanel>
                </>
            )}
        </Popover>
    );
};

const MobileCategoryMenu = ({ category }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <Popover key={category.name} className="flow-root">
            <Popover.Button
                className="group relative -m-2 flex w-full items-center justify-between p-2 text-gray-400 hover:text-gray-500"
                onClick={() => setIsOpen(!isOpen)}
            >
                <span>{category.name}</span>
                <span className="ml-6 flex items-center">
                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L10.168 10 7.23 6.29a.75.75 0 111.04-1.08l3.5 3.36a.75.75 0 010 1.08l-3.5 3.36a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                    </svg>
                </span>
            </Popover.Button>
            {isOpen && (
                <Popover.Panel className="mt-2 space-y-2">
                    {category.subcategories.map((subcategory) => (
                        <div key={subcategory.name}>
                            <h3 className="font-medium text-gray-900">{subcategory.name}</h3>
                            <ul role="list" className="mt-2 space-y-1">
                                {subcategory.items.map((item) => (
                                    <li key={item.name}>
                                        <Link href={item.href} className="block text-gray-500 hover:text-gray-900">
                                            {item.name}
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </Popover.Panel>
            )}
        </Popover>
    );
};

export default function Navbar() {
    const [open, setOpen] = useState(false);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const { isSignedIn } = useUser();
    const [trendingProducts, setTrendingProducts] = useState(null);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);

        const fetchTrending = async () => {
            try {
                const trendingData = await getTrendingProducts();
                const adjustedTrendingData = trendingData.map(item => ({
                    name: item.name,
                    href: `/shop/${item.id}`,
                    imageSrc: item.imageUrl,
                    imageAlt: item.name,
                    category: item.category
                }));
                setTrendingProducts(adjustedTrendingData);

            } catch (error) {
                console.error("Error fetching trending products:", error);
            }
        };
        fetchTrending();
    }, []);



    const toggleSearch = () => {
        setIsSearchOpen(!isSearchOpen);
    };

    return (
        <div className="bg-white">
            {/* Mobile menu */}
            <Dialog open={open} onClose={setOpen} className="relative z-40 lg:hidden">
                <DialogBackdrop
                    transition
                    className="fixed inset-0 bg-black/25 transition-opacity duration-300 ease-linear data-closed:opacity-0"
                />
                <div className="fixed inset-0 z-40 flex">
                    <DialogPanel
                        transition
                        className="relative flex w-full max-w-xs transform flex-col overflow-y-auto bg-white pb-12 shadow-xl transition duration-300 ease-in-out data-closed:-translate-x-full scrollbar-hide"
                    >
                        <div className="flex px-4 pt-5 pb-2">
                            <button
                                type="button"
                                onClick={() => setOpen(false)}
                                className="relative -m-2 inline-flex items-center justify-center rounded-md p-2 text-gray-400 lg:hidden"
                            >
                                <span className="absolute -inset-0.5" />
                                <span className="sr-only">Close menu</span>
                                <XMarkIcon aria-hidden="true" className="size-6" />
                            </button>
                        </div>

                        {/* Mobile Menu Links */}
                        <div className="space-y-6 border-t border-gray-200 py-6 px-4">
                            {navigation.categories.map((category) => (
                                <MobileCategoryMenu key={category.name} category={category} />
                            ))}
                            {navigation.pages.map((page) => (
                                <Link
                                    key={page.name}
                                    href={page.href}
                                    className="-m-2 block p-2 font-medium text-gray-900 hover:bg-gray-50"
                                >
                                    {page.name}
                                </Link>
                            ))}
                        </div>


                        <div className="space-y-6 border-t border-gray-200 py-6 px-4">
                            {isSignedIn ? (
                                <UserButton afterSignOutUrl="/" />
                            ) : (
                                <SignInButton className="-m-2 block p-2 font-medium text-gray-900 hover:bg-purple-50 cursor-pointer">
                                    Sign in
                                </SignInButton>
                            )}
                        </div>

                    </DialogPanel>
                </div>
            </Dialog>

            <header className="sticky top-0 z-10 bg-white shadow-md">
                <p className="flex h-10 items-center justify-center bg-gradient-to-r from-purple-400 to-lavender-400 px-4 text-sm font-medium text-white sm:px-6 lg:px-8">
                    {promotionalMessage}
                </p>

                <nav aria-label="Top" className="mx-auto max-w-8xl px-4 sm:px-6 lg:px-8">
                    <div className="border-b border-gray-200">
                        <div className="flex h-16 items-center">
                            <button
                                type="button"
                                onClick={() => setOpen(true)}
                                className="relative rounded-md bg-white p-2 text-gray-400 lg:hidden"
                            >
                                <span className="absolute -inset-0.5" />
                                <span className="sr-only">Open menu</span>
                                <Bars3Icon aria-hidden="true" className="size-6" />
                            </button>

                            {/* Logo */}
                            <div className="ml-4 flex lg:ml-0">
                                <Link href="/">
                                    <span className="sr-only">AURKIRA</span>
                                    <Image
                                        src="/logo.jpeg"
                                        alt="AURKIRA"
                                        className="h-8 w-auto"
                                        width={32}
                                        height={32}
                                        priority
                                    />
                                </Link>
                            </div>

                            {/* Flyout menus */}
                            <PopoverGroup className="hidden lg:ml-8 lg:block lg:self-stretch">
                                <div className="flex h-full space-x-8">
                                    {navigation.categories.map((category) => (
                                        <CategoryMenu key={category.name} category={category} trendingProducts={trendingProducts} />
                                    ))}

                                    {navigation.pages.map((page) => (
                                        <Link
                                            key={page.name}
                                            href={page.href}
                                            className="flex items-center text-sm font-medium text-gray-700 hover:text-purple-600"
                                        >
                                            {page.name}
                                        </Link>
                                    ))}
                                </div>
                            </PopoverGroup>

                            <div className="ml-auto flex items-center">
                                {/* Conditionally show sign in/out button based on authentication */}
                                <div className="hidden lg:flex lg:flex-1 lg:items-center lg:justify-end lg:space-x-6">
                                    {isSignedIn ? (
                                        <UserButton afterSignOutUrl="/" />
                                    ) : (
                                        <>
                                            <SignInButton className="-m-2 block p-2 font-medium text-gray-900 hover:bg-purple-50 cursor-pointer" />

                                        </>
                                    )}
                                </div>

                                {/* Search */}
                                <div className="flex lg:ml-6">
                                    <button onClick={toggleSearch} className="p-2 text-gray-400 hover:text-gray-500">
                                        <span className="sr-only">Search</span>
                                        <MagnifyingGlassIcon aria-hidden="true" className="size-6" />
                                    </button>
                                </div>

                                {/* Cart */}
                                <div className="ml-4 flow-root lg:ml-6">
                                    <Link href="/cart" className="group -m-2 flex items-center p-2">
                                        <ShoppingBagIcon
                                            aria-hidden="true"
                                            className="size-6 shrink-0 text-gray-400 group-hover:text-gray-500"
                                        />
                                        <span className="ml-2 text-sm font-medium text-gray-700 group-hover:text-gray-800">0</span>
                                        <span className="sr-only">items in cart, view bag</span>
                                    </Link>
                                </div>
                            </div>
                        </div>
                    </div>
                </nav>
            </header>

            {/* Search Overlay */}
            {isSearchOpen && <SearchOverlay onClose={toggleSearch} />}
        </div>
    )
}