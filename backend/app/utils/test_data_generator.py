"""
Test Data Generator Utility

Generates valid test data for various formats commonly used in Hong Kong web applications:
- HKID numbers with valid check digits (MOD 11 algorithm)
- HKID part extraction for split field scenarios
- Hong Kong phone numbers (8 digits, starts with 5-9)
- Unique email addresses

Usage:
    generator = TestDataGenerator()
    
    # Generate full HKID
    hkid = generator.generate_hkid()  # "A123456(3)"
    
    # Extract parts for split fields
    main_part = generator.extract_hkid_part(hkid, "main")   # "A123456"
    check_digit = generator.extract_hkid_part(hkid, "check") # "3"
    
    # Other data types
    phone = generator.generate_phone()  # "91234567"
    email = generator.generate_email()  # "testuser1234@example.com"
"""

import random
import string
from datetime import datetime
from typing import Optional


class TestDataGenerator:
    """Generator for valid test data with support for composite data extraction"""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize test data generator
        
        Args:
            seed: Optional random seed for reproducible data generation
        """
        # Use instance-specific random generator for reproducibility
        self._random = random.Random(seed)
        self._email_counter = 0
    
    def generate_hkid(self) -> str:
        """
        Generate a valid Hong Kong ID (HKID) number with check digit
        
        Format: L######(C) where:
        - L = Letter (A-Z)
        - # = 6 digits
        - C = Check digit (0-9 or A)
        
        Returns:
            str: Valid HKID like "A123456(3)"
        
        Example:
            >>> generator = TestDataGenerator()
            >>> hkid = generator.generate_hkid()
            >>> print(hkid)
            "A123456(3)"
        """
        # Generate random letter (A-Z)
        letter = self._random.choice(string.ascii_uppercase)
        
        # Generate 6 random digits
        digits = ''.join([str(self._random.randint(0, 9)) for _ in range(6)])
        
        # Calculate check digit using MOD 11 algorithm
        check_digit = self._calculate_hkid_check_digit(letter, digits)
        
        # Format: A123456(3)
        return f"{letter}{digits}({check_digit})"
    
    def _calculate_hkid_check_digit(self, letter: str, digits: str) -> str:
        """
        Calculate HKID check digit using MOD 11 algorithm
        
        Algorithm:
        1. Convert letter to number (A=10, B=11, ..., Z=35)
        2. Multiply letter by 8, each digit by weights [7, 6, 5, 4, 3, 2]
        3. Sum all weighted values
        4. Calculate: check = 11 - (sum % 11)
        5. Special cases: 10 → 'A', 11 → '0'
        
        Args:
            letter: Single uppercase letter (A-Z)
            digits: 6-digit string
        
        Returns:
            str: Check digit (0-9 or 'A')
        
        Example:
            >>> generator = TestDataGenerator()
            >>> check = generator._calculate_hkid_check_digit('A', '123456')
            >>> print(check)
            "3"
        """
        # Convert letter to numeric value (A=10, B=11, ..., Z=35)
        letter_value = ord(letter.upper()) - ord('A') + 10
        
        # Weights: letter gets 8, then digits get [7, 6, 5, 4, 3, 2]
        weights = [7, 6, 5, 4, 3, 2]
        
        # Calculate weighted sum: letter * 8 + sum(digit * weight)
        total = letter_value * 8
        
        for i, digit in enumerate(digits):
            total += int(digit) * weights[i]
        
        # Calculate check digit: 11 - (sum % 11)
        remainder = total % 11
        check = 11 - remainder
        
        # Handle special cases
        if check == 10:
            return 'A'
        elif check == 11:
            return '0'
        else:
            return str(check)
    
    @staticmethod
    def extract_hkid_part(hkid: str, part: str) -> str:
        """
        Extract specific part from HKID for split field scenarios
        
        This is critical for web forms that split HKID into multiple fields:
        - Field 1: Main part (A123456)
        - Field 2: Check digit (3)
        
        Args:
            hkid: Full HKID like "A123456(3)"
            part: Part to extract:
                - "main": Letter + 6 digits (A123456)
                - "check": Check digit only (3)
                - "letter": Letter only (A)
                - "digits": 6 digits only (123456)
                - "full": Full HKID with parentheses (A123456(3))
        
        Returns:
            str: Requested part
        
        Raises:
            ValueError: If part is unknown
        
        Example:
            >>> hkid = "A123456(3)"
            >>> TestDataGenerator.extract_hkid_part(hkid, "main")
            "A123456"
            >>> TestDataGenerator.extract_hkid_part(hkid, "check")
            "3"
        """
        # Remove parentheses for easier extraction
        clean = hkid.replace('(', '').replace(')', '')
        
        if part == "main":
            # A123456 (everything except last character)
            return clean[:-1]
        elif part == "check":
            # 3 (last character only)
            return clean[-1]
        elif part == "letter":
            # A (first character only)
            return clean[0]
        elif part == "digits":
            # 123456 (positions 1-6)
            return clean[1:7]
        elif part == "full":
            # A123456(3) (original with parentheses)
            return hkid
        else:
            raise ValueError(f"Unknown HKID part: '{part}'. Valid parts: main, check, letter, digits, full")
    
    @staticmethod
    def validate_hkid(hkid: str) -> bool:
        """
        Validate if HKID has correct format and check digit
        
        Args:
            hkid: HKID to validate (e.g., "A123456(3)")
        
        Returns:
            bool: True if valid, False otherwise
        
        Example:
            >>> TestDataGenerator.validate_hkid("A123456(3)")
            True
            >>> TestDataGenerator.validate_hkid("A123456(9)")  # Wrong check digit
            False
        """
        # Check format: L######(C)
        if len(hkid) != 10:
            return False
        
        if not hkid[0].isalpha():
            return False
        
        if not hkid[1:7].isdigit():
            return False
        
        if hkid[7] != '(' or hkid[9] != ')':
            return False
        
        # Validate check digit
        letter = hkid[0]
        digits = hkid[1:7]
        provided_check = hkid[8]
        
        generator = TestDataGenerator()
        calculated_check = generator._calculate_hkid_check_digit(letter, digits)
        
        return provided_check == calculated_check
    
    def generate_phone(self) -> str:
        """
        Generate a valid Hong Kong phone number
        
        Format: 8 digits starting with 5, 6, 7, 8, or 9
        
        Returns:
            str: Valid HK phone number like "91234567"
        
        Example:
            >>> generator = TestDataGenerator()
            >>> phone = generator.generate_phone()
            >>> print(phone)
            "91234567"
        """
        # First digit: 5-9 (valid HK mobile prefixes)
        first_digit = self._random.choice(['5', '6', '7', '8', '9'])
        
        # Remaining 7 digits
        remaining_digits = ''.join([str(self._random.randint(0, 9)) for _ in range(7)])
        
        return first_digit + remaining_digits
    
    def generate_email(self, domain: str = "example.com") -> str:
        """
        Generate a unique email address
        
        Args:
            domain: Email domain (default: "example.com")
        
        Returns:
            str: Unique email like "testuser1234@example.com"
        
        Example:
            >>> generator = TestDataGenerator()
            >>> email = generator.generate_email()
            >>> print(email)
            "testuser1234@example.com"
        """
        # Increment counter for uniqueness
        self._email_counter += 1
        
        # Add timestamp for additional uniqueness
        timestamp = datetime.now().strftime("%H%M%S")
        
        # Format: testuser{counter}{timestamp}@domain
        username = f"testuser{self._email_counter}{timestamp}"
        
        return f"{username}@{domain}"
    
    def generate_data(self, data_type: str, **kwargs) -> str:
        """
        Generate test data of specified type
        
        Args:
            data_type: Type of data to generate (hkid, phone, email)
            **kwargs: Additional arguments for specific generators
        
        Returns:
            str: Generated data
        
        Raises:
            ValueError: If data_type is unknown
        
        Example:
            >>> generator = TestDataGenerator()
            >>> generator.generate_data("hkid")
            "A123456(3)"
            >>> generator.generate_data("phone")
            "91234567"
            >>> generator.generate_data("email", domain="test.com")
            "testuser1123456@test.com"
        """
        if data_type == "hkid":
            return self.generate_hkid()
        elif data_type == "phone":
            return self.generate_phone()
        elif data_type == "email":
            domain = kwargs.get("domain", "example.com")
            return self.generate_email(domain)
        else:
            raise ValueError(f"Unknown data type: '{data_type}'. Valid types: hkid, phone, email")
