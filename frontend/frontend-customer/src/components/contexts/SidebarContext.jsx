// contexts/SidebarContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';

const SidebarContext = createContext();

export const SidebarProvider = ({ children }) => {
    const [isExpanded, setIsExpanded] = useState(true);
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        const checkMobile = () => {
            const mobile = window.innerWidth < 768;
            setIsMobile(mobile);
            if (mobile) {
                setIsExpanded(false);
            } else {
                setIsExpanded(true);
            }
        };

        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    const toggleSidebar = () => {
        setIsExpanded(!isExpanded);
    };

    return (
        <SidebarContext.Provider value={{
            isExpanded,
            setIsExpanded,
            toggleSidebar,
            isMobile
        }}>
            {children}
        </SidebarContext.Provider>
    );
};

export const useSidebar = () => useContext(SidebarContext);