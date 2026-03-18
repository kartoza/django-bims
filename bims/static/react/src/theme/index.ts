/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Nature-inspired Chakra UI theme for BIMS.
 * Colors derived from South African landscapes, freshwater ecosystems, and biodiversity.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { extendTheme, ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: false,
};

/**
 * Nature-inspired color palette
 * - Primary: Deep river blue (freshwater focus)
 * - Secondary: Fynbos green (South African biodiversity)
 * - Accent: African sunset orange
 * - Earth tones for grounding
 */
const colors = {
  // Primary - Deep River Blue (freshwater ecosystem)
  brand: {
    50: '#e8f4f8',
    100: '#c5e4ed',
    200: '#9fd2e1',
    300: '#79c0d5',
    400: '#5cb2cc',
    500: '#2d8eb8', // Deep river blue - primary
    600: '#247396',
    700: '#1a5774',
    800: '#113c52',
    900: '#082130',
  },

  // Secondary - Fynbos Green (endemic vegetation)
  fynbos: {
    50: '#f0f7f0',
    100: '#d8ebd8',
    200: '#beddbe',
    300: '#a4cfa4',
    400: '#8fc48f',
    500: '#5a9a5a', // Fynbos green
    600: '#487a48',
    700: '#365b36',
    800: '#243c24',
    900: '#121e12',
  },

  // Accent - African Sunset (warmth and vitality)
  sunset: {
    50: '#fff5eb',
    100: '#ffe4cc',
    200: '#ffd0a8',
    300: '#ffbc85',
    400: '#ffab6b',
    500: '#e87c38', // Warm sunset orange
    600: '#c96428',
    700: '#a04c1c',
    800: '#773610',
    900: '#4d2008',
  },

  // Earth - Savanna Brown (grounding)
  earth: {
    50: '#f9f6f3',
    100: '#efe9e0',
    200: '#e3d9cb',
    300: '#d7c9b6',
    400: '#cdbda5',
    500: '#a89272', // Savanna earth
    600: '#8a755a',
    700: '#6b5944',
    800: '#4c3d2e',
    900: '#2d2318',
  },

  // Conservation status colors (IUCN)
  conservation: {
    LC: '#4a9c3a', // Least Concern - healthy green
    NT: '#8cb369', // Near Threatened - yellow-green
    VU: '#f0b429', // Vulnerable - golden yellow
    EN: '#e57b1f', // Endangered - warning orange
    CR: '#c42c2c', // Critically Endangered - alert red
    EW: '#7b3f9e', // Extinct in Wild - somber purple
    EX: '#2d2d2d', // Extinct - charcoal
    DD: '#8e8e8e', // Data Deficient - neutral gray
    NE: '#c9c9c9', // Not Evaluated - light gray
  },

  // Ecosystem type colors (water-inspired)
  ecosystem: {
    river: '#4a90d9',     // Flowing river blue
    wetland: '#5a8a5a',   // Marsh green
    estuary: '#7ab3a2',   // Brackish water teal
    dam: '#6b8bad',       // Reservoir blue-gray
    lake: '#3d7fb8',      // Lake blue
    coastal: '#5ecac9',   // Coastal turquoise
    marine: '#1e5f8a',    // Ocean deep blue
  },

  // Endemism colors
  endemism: {
    endemic: '#b85c38',   // Rich terracotta for endemic
    indigenous: '#5a9a5a', // Native green
    alien: '#9e5252',     // Alert red-brown for invasive
    unknown: '#8e8e8e',   // Neutral gray
  },

  // Water shades
  water: {
    50: '#e6f4f9',
    100: '#b8e0ed',
    200: '#8acce1',
    300: '#5cb8d5',
    400: '#3da9cc',
    500: '#2d8eb8',
    600: '#247396',
    700: '#1a5774',
    800: '#113c52',
    900: '#082130',
  },

  // Background colors
  bg: {
    light: '#f8fafb',
    paper: '#ffffff',
    subtle: '#f0f4f5',
    muted: '#e8ecee',
  },
};

const fonts = {
  heading: '"Source Sans Pro", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
  body: '"Source Sans Pro", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
  mono: '"Source Code Pro", "Roboto Mono", monospace',
};

const shadows = {
  xs: '0 0 0 1px rgba(45, 142, 184, 0.05)',
  sm: '0 1px 2px 0 rgba(45, 142, 184, 0.05)',
  base: '0 1px 3px 0 rgba(45, 142, 184, 0.1), 0 1px 2px 0 rgba(45, 142, 184, 0.06)',
  md: '0 4px 6px -1px rgba(45, 142, 184, 0.1), 0 2px 4px -1px rgba(45, 142, 184, 0.06)',
  lg: '0 10px 15px -3px rgba(45, 142, 184, 0.1), 0 4px 6px -2px rgba(45, 142, 184, 0.05)',
  xl: '0 20px 25px -5px rgba(45, 142, 184, 0.1), 0 10px 10px -5px rgba(45, 142, 184, 0.04)',
  '2xl': '0 25px 50px -12px rgba(45, 142, 184, 0.25)',
  outline: '0 0 0 3px rgba(45, 142, 184, 0.4)',
  inner: 'inset 0 2px 4px 0 rgba(45, 142, 184, 0.06)',
};

const components = {
  Button: {
    baseStyle: {
      fontWeight: '600',
      borderRadius: 'lg',
      transition: 'all 0.2s',
    },
    variants: {
      solid: {
        bg: 'brand.500',
        color: 'white',
        _hover: {
          bg: 'brand.600',
          transform: 'translateY(-1px)',
          boxShadow: 'md',
        },
        _active: {
          bg: 'brand.700',
          transform: 'translateY(0)',
        },
      },
      outline: {
        borderColor: 'brand.500',
        color: 'brand.600',
        borderWidth: '2px',
        _hover: {
          bg: 'brand.50',
          borderColor: 'brand.600',
        },
      },
      ghost: {
        color: 'brand.600',
        _hover: {
          bg: 'brand.50',
        },
      },
      nature: {
        bg: 'fynbos.500',
        color: 'white',
        _hover: {
          bg: 'fynbos.600',
          transform: 'translateY(-1px)',
          boxShadow: 'md',
        },
        _active: {
          bg: 'fynbos.700',
        },
      },
      sunset: {
        bg: 'sunset.500',
        color: 'white',
        _hover: {
          bg: 'sunset.600',
          transform: 'translateY(-1px)',
          boxShadow: 'md',
        },
        _active: {
          bg: 'sunset.700',
        },
      },
    },
    defaultProps: {
      variant: 'solid',
      size: 'md',
    },
  },

  Card: {
    baseStyle: {
      container: {
        borderRadius: 'xl',
        boxShadow: 'base',
        bg: 'white',
        overflow: 'hidden',
        transition: 'all 0.2s',
        _hover: {
          boxShadow: 'lg',
        },
      },
      header: {
        borderBottomWidth: '1px',
        borderColor: 'gray.100',
      },
    },
  },

  Input: {
    variants: {
      outline: {
        field: {
          borderColor: 'gray.200',
          borderRadius: 'lg',
          _focus: {
            borderColor: 'brand.500',
            boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
          },
          _hover: {
            borderColor: 'gray.300',
          },
        },
      },
      filled: {
        field: {
          bg: 'bg.subtle',
          borderRadius: 'lg',
          _focus: {
            bg: 'white',
            borderColor: 'brand.500',
          },
        },
      },
    },
    defaultProps: {
      variant: 'outline',
    },
  },

  Select: {
    variants: {
      outline: {
        field: {
          borderColor: 'gray.200',
          borderRadius: 'lg',
          _focus: {
            borderColor: 'brand.500',
            boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
          },
        },
      },
    },
  },

  Badge: {
    baseStyle: {
      borderRadius: 'full',
      fontWeight: '600',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    },
    variants: {
      conservation: (props: { colorScheme: string }) => ({
        bg: `conservation.${props.colorScheme}`,
        color: 'white',
        fontSize: 'xs',
        px: 3,
        py: 1,
      }),
      ecosystem: (props: { colorScheme: string }) => ({
        bg: `ecosystem.${props.colorScheme}`,
        color: 'white',
        fontSize: 'xs',
        px: 3,
        py: 1,
      }),
      subtle: {
        bg: 'bg.subtle',
        color: 'gray.600',
      },
    },
  },

  Tabs: {
    variants: {
      line: {
        tab: {
          fontWeight: '600',
          _selected: {
            color: 'brand.600',
            borderColor: 'brand.500',
            borderBottomWidth: '3px',
          },
          _hover: {
            color: 'brand.500',
          },
        },
        tablist: {
          borderBottomWidth: '1px',
          borderColor: 'gray.100',
        },
      },
      enclosed: {
        tab: {
          fontWeight: '500',
          borderRadius: 'lg lg 0 0',
          _selected: {
            bg: 'white',
            color: 'brand.600',
            borderColor: 'gray.200',
            borderBottomColor: 'white',
          },
        },
      },
      'soft-rounded': {
        tab: {
          borderRadius: 'full',
          fontWeight: '600',
          _selected: {
            color: 'white',
            bg: 'brand.500',
          },
        },
      },
    },
  },

  Modal: {
    baseStyle: {
      dialog: {
        borderRadius: 'xl',
        boxShadow: '2xl',
      },
      header: {
        fontSize: 'lg',
        fontWeight: '700',
        color: 'gray.800',
      },
    },
  },

  Drawer: {
    baseStyle: {
      dialog: {
        bg: 'white',
      },
      header: {
        borderBottomWidth: '1px',
        borderColor: 'gray.100',
      },
    },
  },

  Heading: {
    baseStyle: {
      color: 'gray.800',
      fontWeight: '700',
    },
  },

  Table: {
    variants: {
      simple: {
        th: {
          borderColor: 'gray.100',
          bg: 'bg.subtle',
          fontWeight: '700',
          textTransform: 'none',
          letterSpacing: 'normal',
          fontSize: 'sm',
          color: 'gray.600',
        },
        td: {
          borderColor: 'gray.100',
        },
        tr: {
          _hover: {
            bg: 'brand.50',
          },
        },
      },
      striped: {
        th: {
          bg: 'bg.subtle',
          fontWeight: '700',
        },
        tr: {
          _odd: {
            bg: 'bg.light',
          },
        },
      },
    },
  },

  Alert: {
    variants: {
      subtle: {
        container: {
          borderRadius: 'lg',
        },
      },
      'left-accent': {
        container: {
          borderRadius: 'lg',
          borderLeftWidth: '4px',
        },
      },
    },
  },

  Stat: {
    baseStyle: {
      container: {
        borderRadius: 'xl',
        bg: 'white',
        boxShadow: 'base',
        p: 4,
      },
      label: {
        fontWeight: '500',
        color: 'gray.500',
        textTransform: 'uppercase',
        fontSize: 'xs',
        letterSpacing: 'wide',
      },
      number: {
        fontWeight: '700',
        color: 'gray.800',
      },
    },
  },

  Menu: {
    baseStyle: {
      list: {
        borderRadius: 'xl',
        boxShadow: 'lg',
        border: '1px solid',
        borderColor: 'gray.100',
        py: 2,
      },
      item: {
        borderRadius: 'lg',
        mx: 2,
        px: 3,
        _hover: {
          bg: 'brand.50',
        },
        _focus: {
          bg: 'brand.50',
        },
      },
    },
  },

  Tooltip: {
    baseStyle: {
      borderRadius: 'lg',
      bg: 'gray.800',
      color: 'white',
      fontWeight: '500',
      px: 3,
      py: 2,
    },
  },
};

const styles = {
  global: {
    'html, body': {
      bg: 'bg.light',
      color: 'gray.800',
    },
    body: {
      lineHeight: '1.6',
    },
    a: {
      color: 'brand.600',
      _hover: {
        color: 'brand.700',
        textDecoration: 'none',
      },
    },
    '::selection': {
      bg: 'brand.100',
      color: 'brand.900',
    },
    '::-webkit-scrollbar': {
      width: '8px',
      height: '8px',
    },
    '::-webkit-scrollbar-track': {
      bg: 'bg.muted',
    },
    '::-webkit-scrollbar-thumb': {
      bg: 'gray.300',
      borderRadius: 'full',
    },
    '::-webkit-scrollbar-thumb:hover': {
      bg: 'gray.400',
    },
  },
};

const breakpoints = {
  sm: '30em',
  md: '48em',
  lg: '62em',
  xl: '80em',
  '2xl': '96em',
};

const radii = {
  none: '0',
  sm: '0.25rem',
  base: '0.375rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
  '2xl': '1.5rem',
  '3xl': '2rem',
  full: '9999px',
};

export const theme = extendTheme({
  config,
  colors,
  fonts,
  shadows,
  components,
  styles,
  breakpoints,
  radii,
});

export default theme;
