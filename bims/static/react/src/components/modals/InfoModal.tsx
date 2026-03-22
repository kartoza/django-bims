/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Info Modal with "Don't show again" option
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React, { useState, useCallback, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  Checkbox,
  Text,
  VStack,
  HStack,
  Icon,
  Box,
} from '@chakra-ui/react';
import { InfoIcon, WarningIcon, CheckCircleIcon, WarningTwoIcon } from '@chakra-ui/icons';

type ModalVariant = 'info' | 'warning' | 'success' | 'error';

interface InfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  variant?: ModalVariant;
  persistKey?: string; // Key for localStorage to remember "don't show again"
  showDontShowAgain?: boolean;
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void;
}

const variantConfig: Record<ModalVariant, { icon: typeof InfoIcon; color: string }> = {
  info: { icon: InfoIcon, color: 'blue.500' },
  warning: { icon: WarningIcon, color: 'orange.500' },
  success: { icon: CheckCircleIcon, color: 'green.500' },
  error: { icon: WarningTwoIcon, color: 'red.500' },
};

const STORAGE_PREFIX = 'bims_modal_hidden_';

export const InfoModal: React.FC<InfoModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  variant = 'info',
  persistKey,
  showDontShowAgain = true,
  confirmText = 'OK',
  cancelText,
  onConfirm,
}) => {
  const [dontShowAgain, setDontShowAgain] = useState(false);
  const [shouldShow, setShouldShow] = useState(true);

  const config = variantConfig[variant];
  const IconComponent = config.icon;

  // Check if modal should be shown based on localStorage
  useEffect(() => {
    if (persistKey) {
      const isHidden = localStorage.getItem(`${STORAGE_PREFIX}${persistKey}`);
      setShouldShow(!isHidden);
    }
  }, [persistKey]);

  const handleClose = useCallback(() => {
    if (dontShowAgain && persistKey) {
      localStorage.setItem(`${STORAGE_PREFIX}${persistKey}`, 'true');
    }
    onClose();
  }, [dontShowAgain, persistKey, onClose]);

  const handleConfirm = useCallback(() => {
    if (dontShowAgain && persistKey) {
      localStorage.setItem(`${STORAGE_PREFIX}${persistKey}`, 'true');
    }
    onConfirm?.();
    onClose();
  }, [dontShowAgain, persistKey, onConfirm, onClose]);

  // Don't render if user chose not to show again
  if (!shouldShow && persistKey) {
    return null;
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <HStack spacing={2}>
            <Icon as={IconComponent} color={config.color} boxSize={5} />
            <Text>{title}</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />

        <ModalBody>
          <VStack spacing={4} align="stretch">
            <Box>{children}</Box>

            {showDontShowAgain && persistKey && (
              <Checkbox
                isChecked={dontShowAgain}
                onChange={(e) => setDontShowAgain(e.target.checked)}
                size="sm"
                colorScheme="gray"
              >
                <Text fontSize="sm" color="gray.600">
                  Don't show this message again
                </Text>
              </Checkbox>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <HStack spacing={2}>
            {cancelText && (
              <Button variant="ghost" onClick={handleClose}>
                {cancelText}
              </Button>
            )}
            <Button colorScheme="blue" onClick={handleConfirm}>
              {confirmText}
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

// Utility function to reset a specific modal's "don't show again" preference
export const resetModalPreference = (persistKey: string): void => {
  localStorage.removeItem(`${STORAGE_PREFIX}${persistKey}`);
};

// Utility function to reset all modal preferences
export const resetAllModalPreferences = (): void => {
  const keys = Object.keys(localStorage);
  keys.forEach((key) => {
    if (key.startsWith(STORAGE_PREFIX)) {
      localStorage.removeItem(key);
    }
  });
};

export default InfoModal;
