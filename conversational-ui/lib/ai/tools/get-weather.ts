import { tool } from 'ai';
import { z } from 'zod';

export const getWeather = tool({
  description: 'Get the current weather at a location',
  parameters: z.object({
    latitude: z.number(),
    longitude: z.number(),
  }),
  // execute function removed to enable human-in-the-loop confirmation
});

// Separate execute function for when user confirms
export const executeWeatherTool = async ({ latitude, longitude }: { latitude: number; longitude: number }) => {
  const response = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m&hourly=temperature_2m&daily=sunrise,sunset&timezone=auto`,
  );

  const weatherData = await response.json();
  return weatherData;
};
