import { createMemo } from '../lib/api';

global.fetch = jest.fn() as jest.Mock;

describe('createMemo', () => {
    beforeEach(() => {
        (global.fetch as jest.Mock).mockClear();
    });

    it('should POST form data and return JSON on success', async () => {
        const mockResponse = { message: 'saved', path: 'memos/test/uuid.txt' };
        (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: true, json: async () => mockResponse });

        const data = await createMemo({ category: 'test', title: 'Hello', tags: 'tag1,tag2', body: 'Body text' });
        expect(global.fetch).toHaveBeenCalledWith(
            'http://localhost:8001/api/memo',
            expect.objectContaining({ method: 'POST', body: expect.any(FormData) })
        );
        expect(data).toEqual(mockResponse);
    });

    it('should throw error on non-OK response', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false, status: 500, statusText: 'Internal Server Error' });
        await expect(createMemo({ category: '', title: '', tags: '', body: '' })).rejects.toThrow(
            'HTTP 500: Internal Server Error'
        );
    });
});
