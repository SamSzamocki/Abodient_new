
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MessageSquare, LayoutDashboard, Database, Settings, Users, BarChart3, LogOut } from 'lucide-react';

interface NavItemProps {
  to: string;
  icon: React.ElementType;
  label: string;
  currentPath: string;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon: Icon, label, currentPath }) => {
  const isActive = currentPath === to || (currentPath.startsWith(to) && to !== "/");
  return (
    <li>
      <Link
        to={to}
        className={`flex items-center py-3 px-4 rounded-lg transition-colors duration-200 ease-in-out
                    ${isActive 
                      ? 'bg-sidebar-primary text-sidebar-primary-foreground' 
                      : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                    }`}
      >
        <Icon className="mr-3 h-5 w-5" />
        <span>{label}</span>
      </Link>
    </li>
  );
};

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navItems = [
    { to: '/chat', icon: MessageSquare, label: 'Chat' },
    { to: '/', icon: LayoutDashboard, label: 'Actions' }, // Was Activity
    { to: '/database', icon: Database, label: 'Database' }, // Was Knowledge, new icon
    { to: '/configuration', icon: Settings, label: 'Configuration' }, // Was Settings
    { to: '/contacts', icon: Users, label: 'Contacts' },
    { to: '/reports', icon: BarChart3, label: 'Reports' },
  ];

  return (
    <aside className="w-64 bg-sidebar text-sidebar-foreground flex flex-col fixed top-0 left-0 h-full shadow-lg z-10">
      <div className="p-6 border-b border-sidebar-border">
        <h1 className="text-2xl font-bold text-sidebar-primary-foreground">Elise<sup className="text-xs text-primary">AI</sup></h1>
      </div>
      <nav className="flex-grow p-4 space-y-2">
        <ul>
          {navItems.map((item) => (
            <NavItem key={item.to} {...item} currentPath={location.pathname} />
          ))}
        </ul>
      </nav>
      <div className="p-4 mt-auto border-t border-sidebar-border">
        {/* Settings link removed from here as it's now Configuration in main nav */}
        <ul>
          <li>
            <button
              className="flex items-center py-3 px-4 rounded-lg transition-colors duration-200 ease-in-out text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground w-full"
            >
              <LogOut className="mr-3 h-5 w-5" />
              <span>Log Out</span>
            </button>
          </li>
        </ul>
      </div>
    </aside>
  );
};

export default Sidebar;
