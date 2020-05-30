import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import sys
from os import path
import os
import cred
from datetime import datetime

info = {'LOGIN_U': cred.LOGIN_U, 'LOGIN_P': cred.LOGIN_P, 'btn_login': '1', 'btn_login': 'Sign+in'}
url = 'https://gosavy.com/en/login/'

# Desired loan parameters for first evaluation
investment = 5  # Desired amount for investment
desired_credit_rating = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']
desired_return_value = 16
desired_fail_rate = 5
desired_job_type = ['Full time', 'Commerce', 'Statutory officer', 'Freelancer', 'Rent income',
                    'Dividends', 'Other']
desired_debts_obligations_status = 'No'

# if there is no file - then create it
if path.exists("approved_loans_list.csv") is False:
    print('failo dar nera')
    df_columns = ['Loan ID', 'Loan Amount', 'Maturity', 'APR interest', 'SAVY credit rating',
                  'Probability to default', 'Funding progress', 'Investment', 'Time', 'Age', 'Gender', 'City',
                  'Purpose of loan', 'Job type', 'Years at current employer',
                  'Occupation', 'Years working in total', 'Education', 'Residence',
                  'Family status', 'Number of dependents',
                  'Property (data from register)', 'Payment day',
                  'Outstanding debts and financial obligations',
                  'Last registered payment of debt and financial obligations', 'Income',
                  'Monthly income EUR', 'Disposable income', 'Debt to income ratio',
                  'Monthly financial obligations', 'of which are', 'Leasing',
                  'Consumer credit loans', 'Mortgage']
    pd.DataFrame(columns=df_columns).set_index('Loan ID').to_csv('approved_loans_list.csv')  # creating file
else:
    print('jau yra failas')
    pass

with requests.Session() as s:
    src = s.get(url)
    connect = s.post(url, data=info)  # Loging in to accout
    while True:
        while True:#have what to break
            main_page = s.get('https://gosavy.com/en/loan-list/')  # downloading desired page
            soup = BeautifulSoup(main_page.content, 'lxml')
            try:
                balance = float(soup.find('span', {'class': 'balance-value'}).text[:-2])
            except AttributeError:
                print('Attribute Error ocured')
                os.execv(sys.executable, ['python'] + sys.argv)  # Restart script if error ocures
            except:
                print('Other Error then atrribute occured')

            if balance < investment:
                print(f'Not enough funds! Funds: {balance}, Investment: {investment}')
                time.sleep(3600)
                break

            dfs = pd.read_html('https://gosavy.com/en/loan-list/', index_col='Loan ID')
            for index in dfs[0].index:
                if len(index) > 6:
                    dfs[0].drop([str(index)], inplace=True)

            dfs[0].dropna(axis='columns', inplace=True)
            df = dfs[0].drop(['Unnamed: 10', 'Funding progress.1'], axis=1)

            for index, row in df.iterrows():
                left_list = row['Funding progress'].replace("€", '').replace(" ", '').split('/')
                left_to_fund = int(int(left_list[1]) - int(left_list[0]))

                default = float(row['Probability to default'][:-1])

                rating = str(row['SAVY credit rating'])

                interest = int(row['APR interest'][:-1])

                if default <= desired_fail_rate and rating in desired_credit_rating and \
                        interest >= desired_return_value and left_to_fund >= investment:
                    print('Buy it!!!')
                    # print(index, row)
                    loan_url = 'https://gosavy.com/en/loan/view/{}/#view'.format(index)
                    loan_url_table = pd.read_html(loan_url)  # read table
                    loan_df = pd.concat([loan_url_table[0], loan_url_table[1]])  # concat 2 tables in 1 dataframe
                    loan_df = pd.DataFrame(loan_df).set_index(1)
                    loan_df.drop(0, inplace=True, axis='columns')  # del columns named 0
                    loan_df = loan_df.T

                    loan_df.rename(index={2: index}, inplace=True)
                    loan_df.index.name = 'Loan ID'

                    debts_and_obligation = loan_df['Outstanding debts and financial obligations'].values[0]
                    job_type = loan_df['Job type'].values[0]

                    if debts_and_obligation == desired_debts_obligations_status and job_type in desired_job_type:
                        print('get it')
                        df_from_file = pd.read_csv('approved_loans_list.csv')
                        if index not in df_from_file.index:  # check if loan is already in file(am I alredy invested in
                            # loan? True=No)
                            print('not in file')
                            loan_buy_url = 'https://gosavy.com/en/loan/view/{}'.format(index)
                            invest_info = {'ITEM[LOAN_ID]': index, 'ITEM[AMOUNT]': str(investment), 'btn_place_bid': '1'}
                            agree_info = {'btn_agree_contract': 'Agree'}
                            agree_url = "https://gosavy.com/en/invest/contract"
                            src_ = s.get(loan_buy_url)

                            buy = s.post(loan_buy_url, data=invest_info)  # Sending payload to url(buying investment)
                            time.sleep(1)
                            agree = s.post(agree_url, data=agree_info)  # agree with terms
                            time_of_buy = datetime.now().strftime("%d/%m/%Y %H:%M:%S")  # time when transaction made

                            full_df = pd.DataFrame(df.loc[index]).T
                            full_df.index.name = 'Loan ID'
                            full_df.loc[[index], 'Investment'] = investment  # add invested amount to purchased loan row
                            full_df.loc[[index], 'Time'] = time_of_buy  # add time to purchased loan row
                            full_df = pd.merge(pd.DataFrame(full_df), loan_df, left_index=True, right_index=True,
                                               sort=False)
                            df_from_file = df_from_file.append(full_df, sort=False).drop(['Loan ID'],
                                                                                         axis=1)  # for columns aligment
                            # in file

                            # saving data about buyed loan in file
                            df_from_file.iloc[[-1]].to_csv('/home/ro/coding/loans/approved_loans_list.csv', mode='a',
                                                           header=False)
                        else:
                            print('Already in file')
                    else:
                        print('Obligations or job type not correct')
                else:
                    print('No loans with desired properties')
                    print(f'Balance: {balance}')
                    time.sleep(45)
