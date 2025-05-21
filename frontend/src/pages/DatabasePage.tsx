
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Database } from 'lucide-react';

const DatabasePage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-foreground">Database</h1>
      <p className="text-muted-foreground mb-6">
        This section will display and manage your database content. Connect to Supabase to interact with your data.
      </p>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Database className="mr-2 h-5 w-5" />
            Database View
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed border-border rounded-lg">
            <Database className="h-16 w-16 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Your database tables and data will appear here.</p>
            <p className="text-sm text-muted-foreground mt-2">
              Please ensure Supabase is connected and tables are set up.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DatabasePage;
