
import React from 'react';

// Simplified heatmap representation for now
const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const hours = Array.from({ length: 24 }, (_, i) => i); // 24 hours

const CallDurationHeatmap: React.FC = () => {
  // Mock data: intensity 0-4
  const mockData = Array(7).fill(0).map(() => Array(24).fill(0).map(() => Math.floor(Math.random() * 5)));

  const getHeatmapColor = (intensity: number) => {
    if (intensity === 0) return 'bg-slate-200 dark:bg-slate-700'; // Using slate for neutral
    if (intensity === 1) return 'bg-primary/20';
    if (intensity === 2) return 'bg-primary/40';
    if (intensity === 3) return 'bg-primary/70';
    return 'bg-primary';
  };

  return (
    <div className="grid grid-cols-7 gap-1 p-2 border border-border rounded-md bg-card">
      {days.map((day, dayIndex) => (
        <div key={day} className="text-center">
          <div className="text-xs text-muted-foreground mb-1">{day}</div>
          {hours.slice(6, 19).map((hour) => { // Displaying a relevant slice of hours (e.g., 6 AM to 6 PM)
            const intensity = mockData[dayIndex][hour];
            return (
              <div
                key={`${day}-${hour}`}
                title={`Activity at ${hour}:00 on ${day}`}
                className={`w-full h-3 my-0.5 rounded-sm ${getHeatmapColor(intensity)}`}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
};

export default CallDurationHeatmap;
