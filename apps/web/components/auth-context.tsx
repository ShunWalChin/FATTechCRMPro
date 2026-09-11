'use client';
import {createContext,useContext} from 'react';
import type {User} from '@/lib/api';
export const AuthContext=createContext<User|null>(null);
export function useUser(){return useContext(AuthContext)}
