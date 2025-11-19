import React from 'react';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className,
  padding = true 
}) => {
  return (
    <div
      className={clsx(
        'bg-white rounded-lg shadow-md border border-gray-200',
        padding && 'p-6',
        className
      )}
    >
      {children}
    </div>
  );
};

