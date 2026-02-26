'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import Loader from '../ui/Loader';

export default function ClientWrapper({ children }) {
  const pathname = usePathname();
  const [showLoader, setShowLoader] = useState(true);
  const [prevPath, setPrevPath] = useState(pathname);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowLoader(false);
    }, 4000); // Minimum 4 seconds loader

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (pathname !== prevPath) {
      setShowLoader(true);
      setPrevPath(pathname);
      const timer = setTimeout(() => setShowLoader(false), 4000);
      return () => clearTimeout(timer);
    }
  }, [pathname]);

  return (
    <>
      {showLoader && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-white">
          <Loader />
        </div>
      )}
      <div style={{ display: showLoader ? 'none' : 'block' }}>{children}</div>
    </>
  );
}
