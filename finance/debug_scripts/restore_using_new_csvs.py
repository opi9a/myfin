# myfin/debug_scripts/restore_using_new_csvs.py

def restore_using_new_csvs(new_csv_path=Path('new_csvs'), file_ext='.pdf',
                           delete_csvs=False):
    """
    Looks in new_csv_path for new csv files, and moves the corresponding 
    pre_csv file from processed_pre_csvs to new_pre_csvs    
    """

    print('restoring csvs in', new_csv_path)

    pdf_paths = []
    for csv in Path('new_csvs').iterdir(): 
        pdf_name = csv.name.replace('.csv', file_ext) 
        pdf_paths.append(Path('processed_pre_csvs', pdf_name))


    print('\nwill look for these pre_csvs:')
    print()

    for pdf_path in pdf_paths:
        print(' -', str(pdf_path).ljust(25), 'Exists:', pdf_path.exists())

    if input('\nrestore these to new_processed_csvs? ').lower() == 'y':
        print('\nok')
        for pdf_path in pdf_paths:
            if not pdf_path.exists():
                print('cannot find', str(pdf_path), 'to move it')
                continue
            new_path = Path('new_pre_csvs', pdf_path.name)
            print('renaming to', new_path)
            pdf_path.rename(new_path)
            print('success', new_path.exists())



    else:
        print('\nexiting')

