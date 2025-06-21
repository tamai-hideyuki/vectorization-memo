import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Home from '../pages/index';
import * as api from '../lib/api';

// Mock the entire module
jest.mock('../lib/api');
const createMemoMock = api.createMemo as jest.Mock;

describe('Home component', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders form and submits data', async () => {
        // Arrange: mock resolved value
        createMemoMock.mockResolvedValueOnce({ message: 'saved', path: 'memos/test/uuid.txt' });

        // Act
        render(<Home />);
        fireEvent.change(screen.getByPlaceholderText('カテゴリ'), { target: { value: 'testCat' } });
        fireEvent.change(screen.getByPlaceholderText('タイトル'), { target: { value: 'testTitle' } });
        fireEvent.change(screen.getByPlaceholderText('タグ (カンマ区切り)'), { target: { value: 'tag1,tag2' } });
        fireEvent.change(screen.getByPlaceholderText('本文'), { target: { value: 'body text' } });
        fireEvent.click(screen.getByRole('button', { name: '保存' }));

        // Assert: createMemo was called correctly
        expect(createMemoMock).toHaveBeenCalledWith({ category: 'testCat', title: 'testTitle', tags: 'tag1,tag2', body: 'body text' });

        // Assert: saved result is displayed
        await waitFor(() => screen.getByText('保存結果'));
        expect(screen.getByText(/saved/)).toBeInTheDocument();
        expect(screen.getByText(/memos\/test\/uuid.txt/)).toBeInTheDocument();
    });

    it('shows error message on API failure', async () => {
        // Arrange: mock rejected value
        createMemoMock.mockRejectedValueOnce(new Error('fail'));

        // Act
        render(<Home />);
        fireEvent.change(screen.getByPlaceholderText('カテゴリ'), { target: { value: 'c' } });
        fireEvent.change(screen.getByPlaceholderText('タイトル'), { target: { value: 't' } });
        fireEvent.change(screen.getByPlaceholderText('本文'), { target: { value: 'b' } });
        fireEvent.click(screen.getByRole('button', { name: '保存' }));

        // Assert: error is displayed
        await waitFor(() => expect(screen.getByText('エラー: fail')).toBeInTheDocument());
    });
});
