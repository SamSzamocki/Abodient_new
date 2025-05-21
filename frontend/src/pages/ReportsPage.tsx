
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import CallVolumeChart from '@/components/reports/CallVolumeChart';
import CallDurationHeatmap from '@/components/reports/CallDurationHeatmap';

const ReportsPage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-foreground">Reporting</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Call Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-primary">987,867</p>
            <p className="text-sm text-muted-foreground">Total calls</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Median Call Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-primary">62s</p>
            <p className="text-sm text-muted-foreground">Average time</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Daily Number of Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <CallVolumeChart />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Daily Call Activity</CardTitle>
            <CardDescription className="text-sm">Heatmap of call times</CardDescription>
          </CardHeader>
          <CardContent>
            <CallDurationHeatmap />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ReportsPage;
