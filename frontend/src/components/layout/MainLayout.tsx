
import React from 'react';
import Sidebar from './Sidebar';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-grow p-8 ml-64"> {/* Add ml-64 to offset sidebar width */}
        {children}
      </main>
    </div>
  );
};

export default MainLayout;
