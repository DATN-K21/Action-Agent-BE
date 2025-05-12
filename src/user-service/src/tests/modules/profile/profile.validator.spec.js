const validator = require('validator');
const ProfileValidator = require('../../../modules/profile/profile.validator');

describe('ProfileValidator', () => {
  describe('validateOptionalAttributes', () => {
    // it('should validate optional attributes successfully', () => {
    //   const dataSource = {
    //     nickname: 'testnickname',
    //     bio: 'test bio',
    //     gender: 'male',
    //     date_of_birth: '1990-01-01',
    //     avatar: 'http://example.com/avatar.jpg',
    //     cover_photo: 'http://example.com/cover.jpg',
    //     email: 'test@example.com',
    //     phone: '1234567890',
    //     address: {
    //       street: '123 Test St',
    //       city: 'Test City',
    //       state: 'Test State',
    //       country: 'Test Country',
    //       postal_code: '12345'
    //     },
    //     social: {
    //       name: 'facebook',
    //       url: 'http://facebook.com/test'
    //     },
    //     workplace: 'Test Workplace',
    //     education: 'Test Education'
    //   };

    //   const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050105);
    //   expect(result.error).toBe(false);
    //   expect(result.data.validatedOptionalData).toBeDefined();
    // });
    it('should validate optional attributes successfully', () => {
      const dataSource = {
        nickname: 'testnickname',
        bio: 'test bio',
        gender: 'male',
        date_of_birth: '1990-01-01',
        avatar: 'http://example.com/avatar.jpg',
        cover_photo: 'http://example.com/cover.jpg',
        email: 'test@example.com',
        phone: '1234567890',
        address: {
          street: '123 Test St',
          city: 'Test City',
          state: 'Test State',
          country: 'Test Country',
          postal_code: '12345'
        },
        social: {
          name: 'facebook',
          url: 'http://facebook.com/test'
        },
        workplace: 'Test Workplace',
        education: 'Test Education'
      };

      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050105);
      expect(result.error).toBe(false);
      expect(result.data.validatedOptionalData).toBeDefined();
    });


    it('should return error for invalid nickname length', () => {
      const dataSource = { nickname: 'ab' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050105);
      expect(result.error).toBe(true);
      expect(result.message).toBe('The length of nickname must between 3 and 100');
    });

    it('should return error for invalid bio length', () => {
      const dataSource = { bio: 'ab' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050106);
      expect(result.error).toBe(true);
      expect(result.message).toBe('The length of bio must between 3 and 500');
    });

    it('should return error for invalid gender', () => {
      const dataSource = { gender: 'invalid' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050107);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Gender is invalid');
    });

    it('should return error for invalid date of birth', () => {
      const dataSource = { date_of_birth: 'invalid-date' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050108);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Date of birth is invalid');
    });

    it('should return error for future date of birth', () => {
      const dataSource = { date_of_birth: '3000-01-01' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050109);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Date of birth must be less than current date');
    });

    it('should return error for underage date of birth', () => {
      const dataSource = { date_of_birth: '2010-01-01' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050110);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Date of birth must be at least 18 years old');
    });

    it('should return error for invalid avatar URL', () => {
      const dataSource = { avatar: 'invalid-url' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050111);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Avatar URL is invalid');
    });

    it('should return error for invalid cover photo URL', () => {
      const dataSource = { cover_photo: 'invalid-url' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050112);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Cover photo URL is invalid');
    });

    it('should return error for invalid email', () => {
      const dataSource = { email: 'invalid-email' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050113);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Email is invalid');
    });

    it('should return error for invalid phone', () => {
      const dataSource = { phone: 'invalid-phone' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050114);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Phone is invalid');
    });

    it('should return error for invalid address street length', () => {
      const dataSource = { address: { street: 'ab' } };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050115);
      expect(result.error).toBe(true);
      expect(result.message).toBe('The length of address street must between 3 and 100');
    });

    it('should return error for invalid social name', () => {
      const dataSource = { social: { name: 'invalid' } };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050116);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Social URL is required');
    });

    it('should return error for invalid social URL', () => {
      const dataSource = { social: { url: 'invalid-url' } };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050117);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Social name is required');
    });

    it('should return error for invalid workplace length', () => {
      const dataSource = { workplace: 'ab' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050118);
      expect(result.error).toBe(true);
      expect(result.message).toBe('The length of workplace must between 3 and 100');
    });

    it('should return error for invalid education length', () => {
      const dataSource = { education: 'ab' };
      const result = ProfileValidator.validateOptionalAttributes(dataSource, 1050119);
      expect(result.error).toBe(true);
      expect(result.message).toBe('The length of education must between 3 and 100');
    });
  });

  describe('validateCreateNewProfile', () => {
    it('should validate create new profile successfully', () => {
      const req = {
        body: {
          user_id: '60d0fe4f5311236168a109ca',
          email: 'test@example.com',
          nickname: 'testnickname',
          bio: 'test bio',
          gender: 'male',
          date_of_birth: '1990-01-01',
          avatar: 'http://example.com/avatar.jpg',
          cover_photo: 'http://example.com/cover.jpg',
          phone: '1234567890',
          address: {
            street: '123 Test St',
            city: 'Test City',
            state: 'Test State',
            country: 'Test Country',
            postal_code: '12345'
          },
          social: {
            name: 'facebook',
            url: 'http://facebook.com/test'
          },
          workplace: 'Test Workplace',
          education: 'Test Education'
        }
      };

      const result = ProfileValidator.validateCreateNewProfile(req);
      expect(result.error).toBe(false);
      expect(result.data.profileData).toBeDefined();
    });

    it('should return error for missing user ID', () => {
      const req = { body: { email: 'test@example.com' } };
      const result = ProfileValidator.validateCreateNewProfile(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('User ID is required');
    });

    it('should return error for invalid user ID', () => {
      const req = { body: { user_id: 'invalid-id', email: 'test@example.com' } };
      const result = ProfileValidator.validateCreateNewProfile(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('User ID is invalid');
    });

    it('should return error for missing email', () => {
      const req = { body: { user_id: '60d0fe4f5311236168a109ca' } };
      const result = ProfileValidator.validateCreateNewProfile(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Profile email is required');
    });

    it('should return error for invalid email', () => {
      const req = { body: { user_id: '60d0fe4f5311236168a109ca', email: 'invalid-email' } };
      const result = ProfileValidator.validateCreateNewProfile(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Profile email is invalid');
    });
  });

  describe('validateGetProfileList', () => {
    it('should validate get profile list successfully', () => {
      const req = { query: { limit: '10', page: '1', search: 'test', sort: 'nickname', sortOrder: '1' } };
      const result = ProfileValidator.validateGetProfileList(req);
      expect(result.error).toBe(false);
      expect(result.data.filter).toBeDefined();
    });

    it('should return error for invalid limit', () => {
      const req = { query: { limit: 'invalid' } };
      const result = ProfileValidator.validateGetProfileList(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Limit must be an integer');
    });

    it('should return error for invalid page', () => {
      const req = { query: { page: 'invalid' } };
      const result = ProfileValidator.validateGetProfileList(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Page must be an integer');
    });

    it('should return error for invalid sort attribute', () => {
      const req = { query: { sort: 'invalid' } };
      const result = ProfileValidator.validateGetProfileList(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Sorted attribute is invalid');
    });

    it('should return error for sort order without sort', () => {
      const req = { query: { sortOrder: '1' } };
      const result = ProfileValidator.validateGetProfileList(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Sort order can only be used when sort is given');
    });

    it('should return error for invalid sort order', () => {
      const req = { query: { sort: 'username', sortOrder: 'invalid' } };
      const result = ProfileValidator.validateGetProfileList(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Sorted attribute is invalid');
    });
  });

  describe('validateGetProfileById', () => {
    it('should validate get profile by id successfully', () => {
      const req = { params: { id: '60d0fe4f5311236168a109ca' } };
      const result = ProfileValidator.validateGetProfileById(req);
      expect(result.error).toBe(false);
      expect(result.data.profileId).toBeDefined();
    });

    it('should return error for missing profile ID', () => {
      const req = { params: {} };
      const result = ProfileValidator.validateGetProfileById(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Profile ID is required');
    });

    it('should return error for invalid profile ID', () => {
      const req = { params: { id: 'invalid-id' } };
      const result = ProfileValidator.validateGetProfileById(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Profile ID is invalid');
    });
  });

  describe('validateUpdateProfile', () => {
    it('should validate update profile successfully', () => {
      const req = {
        params: { id: '60d0fe4f5311236168a109ca' },
        body: {
          nickname: 'testnickname',
          bio: 'test bio',
          gender: 'male',
          date_of_birth: '1990-01-01',
          avatar: 'http://example.com/avatar.jpg',
          cover_photo: 'http://example.com/cover.jpg',
          email: 'test@example.com',
          phone: '1234567890',
          address: {
            street: '123 Test St',
            city: 'Test City',
            state: 'Test State',
            country: 'Test Country',
            postal_code: '12345'
          },
          social: {
            name: 'facebook',
            url: 'http://facebook.com/test'
          },
          workplace: 'Test Workplace',
          education: 'Test Education'
        }
      };

      const result = ProfileValidator.validateUpdateProfile(req);
      expect(result.error).toBe(false);
      expect(result.data.profileData).toBeDefined();
    });

    it('should return error for missing profile ID', () => {
      const req = { params: {}, body: {} };
      const result = ProfileValidator.validateUpdateProfile(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Profile ID is required');
    });

    it('should return error for invalid profile ID', () => {
      const req = { params: { id: 'invalid-id' }, body: {} };
      const result = ProfileValidator.validateUpdateProfile(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Profile ID is invalid');
    });
  });

  describe('validateDeleteProfile', () => {
    it('should validate delete profile successfully', () => {
      const req = { params: { id: '60d0fe4f5311236168a109ca' } };
      const result = ProfileValidator.validateDeleteProfile(req);
      expect(result.error).toBe(false);
      expect(result.data.profileId).toBeDefined();
    });

    it('should return error for missing profile ID', () => {
      const req = { params: {} };
      const result = ProfileValidator.validateDeleteProfile(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Profile ID is required');
    });

    it('should return error for invalid profile ID', () => {
      const req = { params: { id: 'invalid-id' } };
      const result = ProfileValidator.validateDeleteProfile(req);
      expect(result.error).toBe(true);
      expect(result.message).toBe('Profile ID is invalid');
    });
  });
});