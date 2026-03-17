/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Chakra UI theme configuration for BIMS.
 * Matches existing BIMS branding while providing modern design tokens.
 */
import { extendTheme, ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: false,
};

const colors = {
  // Primary brand colors matching BIMS
  brand: {
    50: '#e6f2ff',
    100: '#b3d9ff',
    200: '#80bfff',
    300: '#4da6ff',
    400: '#1a8cff',
    500: '#0073e6', // Primary BIMS blue
    600: '#005cb3',
    700: '#004680',
    800: '#002f4d',
    900: '#00191a',
  },
  // Secondary colors
  accent: {
    50: '#e6fff9',
    100: '#b3ffec',
    200: '#80ffdf',
    300: '#4dffd2',
    400: '#1affc5',
    500: '#00e6ac', // Accent green
    600: '#00b386',
    700: '#008060',
    800: '#004d3a',
    900: '#001a14',
  },
  // Conservation status colors
  conservation: {
    LC: '#009900', // Least Concern - green
    NT: '#99cc00', // Near Threatened - yellow-green
    VU: '#ffcc00', // Vulnerable - yellow
    EN: '#ff9900', // Endangered - orange
    CR: '#cc0000', // Critically Endangered - red
    EW: '#6600cc', // Extinct in Wild - purple
    EX: '#333333', // Extinct - dark gray
    DD: '#999999', // Data Deficient - gray
    NE: '#cccccc', // Not Evaluated - light gray
  },
  // Ecosystem type colors
  ecosystem: {
    river: '#4a90d9',
    wetland: '#7ab55c',
    estuary: '#d4a574',
    dam: '#8b7355',
    lake: '#5bb5d9',
  },
};

const fonts = {
  heading: '"Roboto", "Helvetica Neue", Arial, sans-serif',
  body: '"Roboto", "Helvetica Neue", Arial, sans-serif',
  mono: '"Roboto Mono", monospace',
};

const components = {
  Button: {
    baseStyle: {
      fontWeight: '500',
      borderRadius: 'md',
    },
    variants: {
      solid: {
        bg: 'brand.500',
        color: 'white',
        _hover: {
          bg: 'brand.600',
        },
        _active: {
          bg: 'brand.700',
        },
      },
      outline: {
        borderColor: 'brand.500',
        color: 'brand.500',
        _hover: {
          bg: 'brand.50',
        },
      },
      ghost: {
        color: 'brand.500',
        _hover: {
          bg: 'brand.50',
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
        borderRadius: 'lg',
        boxShadow: 'sm',
        bg: 'white',
      },
    },
  },
  Input: {
    variants: {
      outline: {
        field: {
          borderColor: 'gray.300',
          _focus: {
            borderColor: 'brand.500',
            boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
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
          borderColor: 'gray.300',
          _focus: {
            borderColor: 'brand.500',
            boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
          },
        },
      },
    },
  },
  Badge: {
    variants: {
      conservation: (props: { colorScheme: string }) => ({
        bg: `conservation.${props.colorScheme}`,
        color: 'white',
        fontWeight: '600',
        fontSize: 'xs',
        px: 2,
        py: 1,
        borderRadius: 'md',
      }),
    },
  },
  Tabs: {
    variants: {
      line: {
        tab: {
          _selected: {
            color: 'brand.500',
            borderColor: 'brand.500',
          },
        },
      },
    },
  },
  Modal: {
    baseStyle: {
      dialog: {
        borderRadius: 'lg',
      },
    },
  },
  Drawer: {
    baseStyle: {
      dialog: {
        bg: 'white',
      },
    },
  },
};

const styles = {
  global: {
    body: {
      bg: 'gray.50',
      color: 'gray.800',
    },
    a: {
      color: 'brand.500',
      _hover: {
        textDecoration: 'underline',
      },
    },
  },
};

const breakpoints = {
  sm: '30em', // 480px
  md: '48em', // 768px
  lg: '62em', // 992px
  xl: '80em', // 1280px
  '2xl': '96em', // 1536px
};

const space = {
  px: '1px',
  0.5: '0.125rem',
  1: '0.25rem',
  1.5: '0.375rem',
  2: '0.5rem',
  2.5: '0.625rem',
  3: '0.75rem',
  3.5: '0.875rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  7: '1.75rem',
  8: '2rem',
  9: '2.25rem',
  10: '2.5rem',
  12: '3rem',
  14: '3.5rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
  28: '7rem',
  32: '8rem',
  36: '9rem',
  40: '10rem',
  44: '11rem',
  48: '12rem',
  52: '13rem',
  56: '14rem',
  60: '15rem',
  64: '16rem',
  72: '18rem',
  80: '20rem',
  96: '24rem',
};

export const theme = extendTheme({
  config,
  colors,
  fonts,
  components,
  styles,
  breakpoints,
  space,
});

export default theme;
