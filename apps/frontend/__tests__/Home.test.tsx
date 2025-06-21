import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Home from '../pages/index';
import * as api from '../lib/api';

describe('Home component', () => {
    it('renders form and submits data', async () => {
        const spy = jest.spyOn(api, 'createMemo').mockResolvedValueOnce({ message: 'saved', path: 'memos/test/uuid.txt' });
        render(<Home />);

        fireEvent.change(screen.getByPlaceholderText('カテゴリ'), { target: { value: 'testCat' } });
        fireEvent.change(screen.getByPlaceholderText('タイトル'), { target: { value: 'testTitle' } });
        fireEvent.change(screen.getByPlaceholderText('タグ (カンマ区切り)'), { target: { value: 'tag1,tag2' } });
        fireEvent.change(screen.getByPlaceholderText('本文'), { target: { value: 'body text' } });

        fireEvent.click(screen.getByRole('button', { name: '保存' }));
        expect(spy).toHaveBeenCalledWith({ category: 'testCat', title: 'testTitle', tags: 'tag1,tag2', body: 'body text' });

        await waitFor(() => screen.getByText('保存結果'));
        expect(screen.getByText(/saved/)).toBeInTheDocument();
        expect(screen.getByText(/memos\/test\/uuid.txt/)).toBeInTheDocument();
        spy.mockRestore();
    });

    it('shows error message on API failure', async () => {
        jest.spyOn(api, 'createMemo').mockRejectedValueOnce(new Error('fail'));
        render(<Home />);

        fireEvent.change(screen.getByPlaceholderText('カテゴリ'), { target: { value: 'c' } });
        fireEvent.change(screen.getByPlaceholderText('タイトル'), { target: { value: 't' } });
        fireEvent.change(screen.getByPlaceholderText('本文'), { target: { value: 'b' } });

        fireEvent.click(screen.getByRole('button', { name: '保存' }));
        await waitFor(() => expect(screen.getByText('エラー: fail')).toBeInTheDocument());
    });
});
