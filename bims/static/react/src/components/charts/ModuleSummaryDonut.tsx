/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Conservation status donut chart for module summary.
 * Displays IUCN conservation status breakdown with animated entry.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useRef, useEffect, useState } from 'react';
import { Box, Image, Text, VStack, HStack, Flex } from '@chakra-ui/react';
import { keyframes } from '@emotion/react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

// IUCN Conservation Status colors
export const IUCN_COLORS: Record<string, string> = {
  'Critically Endangered': '#B00000',
  'CR': '#B00000',
  'Endangered': '#D00000',
  'EN': '#D00000',
  'Vulnerable': '#FF0000',
  'VU': '#FF0000',
  'Near Threatened': '#FFC000',
  'NT': '#FFC000',
  'Least Concern': '#009106',
  'LC': '#009106',
  'Data Deficient': '#808000',
  'DD': '#808000',
  'Not Evaluated': '#888888',
  'NE': '#888888',
};

// Animation for chart entry
const fadeIn = keyframes`
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
`;

const rotateIn = keyframes`
  from { opacity: 0; transform: rotate(-90deg); }
  to { opacity: 1; transform: rotate(0deg); }
`;

export interface ConservationStatusData {
  chart_data: Record<string, number>;
  colors: string[];
}

interface ModuleSummaryDonutProps {
  name: string;
  icon?: string;
  total: number;
  totalSite: number;
  totalSiteVisit?: number;
  totalSass?: number;
  conservationStatus?: ConservationStatusData;
  delay?: number;
  onClick?: () => void;
}

const ModuleSummaryDonut: React.FC<ModuleSummaryDonutProps> = ({
  name,
  icon,
  total,
  totalSite,
  totalSiteVisit,
  totalSass,
  conservationStatus,
  delay = 0,
  onClick,
}) => {
  const chartRef = useRef<any>(null);
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Intersection observer for animate on scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setTimeout(() => setIsVisible(true), delay);
          }
        });
      },
      { threshold: 0.2 }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, [delay]);

  // Prepare chart data
  const chartData = conservationStatus?.chart_data || {};
  const labels = Object.keys(chartData);
  const values = Object.values(chartData);
  const hasChartData = labels.length > 0 && values.some(v => v > 0);

  // Use colors from API or fallback to default IUCN colors
  const colors = conservationStatus?.colors?.length
    ? conservationStatus.colors
    : labels.map((label) => IUCN_COLORS[label] || '#888888');

  // Fallback data for empty charts - show a gray ring
  const fallbackData = {
    labels: ['No data'],
    datasets: [{
      data: [1],
      backgroundColor: ['#e2e8f0'],
      borderColor: ['#fff'],
      borderWidth: 2,
    }],
  };

  const data = {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: colors,
        borderColor: colors.map(() => '#fff'),
        borderWidth: 2,
        hoverBorderWidth: 3,
        hoverOffset: 8,
      },
    ],
  };

  const options = {
    cutout: '70%',
    responsive: true,
    maintainAspectRatio: true,
    animation: {
      animateRotate: true,
      animateScale: true,
      duration: 1200,
      easing: 'easeOutQuart' as const,
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: { size: 14, weight: 'bold' as const },
        bodyFont: { size: 13 },
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: (context: any) => {
            const value = context.raw;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return ` ${value.toLocaleString()} (${percentage}%)`;
          },
        },
      },
    },
  };

  // Format numbers with commas
  const formatNumber = (num: number) => num.toLocaleString();

  return (
    <Box
      ref={containerRef}
      position="relative"
      textAlign="center"
      cursor={onClick ? 'pointer' : 'default'}
      onClick={onClick}
      opacity={isVisible ? 1 : 0}
      transform={isVisible ? 'scale(1)' : 'scale(0.8)'}
      transition="all 0.6s cubic-bezier(0.4, 0, 0.2, 1)"
      _hover={onClick ? {
        transform: 'scale(1.02)',
        '& .chart-wrapper': {
          boxShadow: '0 8px 30px rgba(0, 0, 0, 0.15)',
        },
      } : {}}
    >
      {/* Chart container with icon overlay */}
      <Box
        className="chart-wrapper"
        position="relative"
        w="150px"
        h="150px"
        mx="auto"
        mb={4}
        transition="box-shadow 0.3s"
      >
        {/* Donut chart */}
        <Box
          animation={isVisible ? `${rotateIn} 0.8s ease-out` : undefined}
        >
          <Doughnut ref={chartRef} data={hasChartData ? data : fallbackData} options={options} />
        </Box>

        {/* Center icon overlay */}
        <Flex
          position="absolute"
          top="50%"
          left="50%"
          transform="translate(-50%, -50%)"
          w="60%"
          h="60%"
          align="center"
          justify="center"
          borderRadius="full"
          bg="white"
          boxShadow="0 2px 8px rgba(0, 0, 0, 0.1)"
          animation={isVisible ? `${fadeIn} 0.6s ease-out 0.3s both` : undefined}
        >
          {icon ? (
            <Image
              src={icon}
              alt={name}
              boxSize="70%"
              objectFit="contain"
            />
          ) : (
            <Text fontSize="2xl" fontWeight="bold" color="gray.600">
              {name.charAt(0)}
            </Text>
          )}
        </Flex>
      </Box>

      {/* Module name */}
      <Text
        fontSize="lg"
        fontWeight="bold"
        color="gray.800"
        mb={2}
        animation={isVisible ? `${fadeIn} 0.5s ease-out 0.2s both` : undefined}
      >
        {name}
      </Text>

      {/* Statistics */}
      <VStack
        spacing={1}
        animation={isVisible ? `${fadeIn} 0.5s ease-out 0.4s both` : undefined}
      >
        <HStack spacing={1} fontSize="sm">
          <Text fontWeight="bold" color="brand.600">
            {formatNumber(total)}
          </Text>
          <Text color="gray.600">Records</Text>
        </HStack>

        <HStack spacing={1} fontSize="sm">
          <Text fontWeight="bold" color="brand.600">
            {formatNumber(totalSite)}
          </Text>
          <Text color="gray.600">Sites</Text>
        </HStack>

        {totalSiteVisit !== undefined && totalSiteVisit > 0 && (
          <HStack spacing={1} fontSize="sm">
            <Text fontWeight="bold" color="brand.600">
              {formatNumber(totalSiteVisit)}
            </Text>
            <Text color="gray.600">Site Visits</Text>
          </HStack>
        )}

        {totalSass !== undefined && totalSass > 0 && (
          <HStack spacing={1} fontSize="sm">
            <Text fontWeight="bold" color="teal.600">
              {formatNumber(totalSass)}
            </Text>
            <Text color="gray.600">SASS Assessments</Text>
          </HStack>
        )}
      </VStack>
    </Box>
  );
};

export default ModuleSummaryDonut;
