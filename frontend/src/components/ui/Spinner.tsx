import React from 'react';

// A simple CSS spinner
const Spinner: React.FC = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '2rem' }}>
    <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-primary"></div>
  </div>
);

export default Spinner; 