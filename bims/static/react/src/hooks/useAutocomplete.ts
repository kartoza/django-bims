/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Hook for autocomplete/typeahead functionality.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import { useState, useCallback, useRef } from 'react';
import { autocompleteApi } from '../api/client';

export interface AutocompleteItem {
  id: number | string;
  name: string;
  [key: string]: unknown;
}

export interface UseAutocompleteOptions {
  type: 'collectors' | 'taxa' | 'sites';
  debounceMs?: number;
  minChars?: number;
  taxonGroup?: string;
}

export interface UseAutocompleteResult {
  query: string;
  setQuery: (query: string) => void;
  results: AutocompleteItem[];
  isLoading: boolean;
  error: string | null;
  clear: () => void;
}

export function useAutocomplete({
  type,
  debounceMs = 300,
  minChars = 2,
  taxonGroup,
}: UseAutocompleteOptions): UseAutocompleteResult {
  const [query, setQueryState] = useState('');
  const [results, setResults] = useState<AutocompleteItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const search = useCallback(
    async (searchQuery: string) => {
      if (searchQuery.length < minChars) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        let data: AutocompleteItem[] = [];

        switch (type) {
          case 'collectors':
            data = await autocompleteApi.collectors(searchQuery);
            break;
          case 'taxa':
            data = await autocompleteApi.taxa(searchQuery, taxonGroup);
            break;
          case 'sites':
            data = await autocompleteApi.sites(searchQuery);
            break;
        }

        setResults(data);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Autocomplete failed';
        setError(errorMessage);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    },
    [type, minChars, taxonGroup]
  );

  const setQuery = useCallback(
    (newQuery: string) => {
      setQueryState(newQuery);

      // Clear previous debounce
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      // Debounce the search
      debounceRef.current = setTimeout(() => {
        search(newQuery);
      }, debounceMs);
    },
    [search, debounceMs]
  );

  const clear = useCallback(() => {
    setQueryState('');
    setResults([]);
    setError(null);
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
  }, []);

  return {
    query,
    setQuery,
    results,
    isLoading,
    error,
    clear,
  };
}

export default useAutocomplete;
